# src/nxcmd/model.py
import json
from pathlib import Path
from collections import defaultdict, Counter
import time
import re

class LocalWorldModel:
    def __init__(self, log_path="~/.wm_shell/history.jsonl"):
        # 展开用户目录路径，如 ~/.wm_shell/ 展开为 /home/username/.wm_shell/
        self.log_path = Path(log_path).expanduser()
        # 转移表数据结构: { (前一个命令, 前前一个命令): Counter({下一个命令: 出现次数}) }
        # 例如: {('git', 'add'): Counter({'git commit': 5, 'git status': 2})}
        self.transitions = defaultdict(Counter)

    def load_and_train(self):
        """从日志文件加载数据并训练 n-gram 模型"""
        # 第一步：将日志按会话切分（10分钟无操作视为新会话）
        sessions = self._parse_logs_into_sessions()
        # 第二步：对每个会话训练 n-gram 模型
        for session in sessions:
            self._train_on_session(session)
        print(f"训练完成，学习了 {len(self.transitions)} 个命令模式")

    def _parse_logs_into_sessions(self):
        """
        将连续的日志记录按时间间隔切分成独立的会话
        逻辑：如果两个命令之间间隔超过10分钟（600秒），就认为是新的会话
        """
        if not self.log_path.exists():
            print("日志文件不存在，跳过训练")
            return []
        
        sessions = []  # 存储所有会话的列表
        current_session = []  # 当前正在构建的会话
        last_ts = 0  # 上一个命令的时间戳

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # 修复：先尝试修复常见的JSON格式问题
                line = line.strip()
                if not line:
                    continue
                    
                # 尝试修复引号嵌套问题
                line = self._fix_json_line(line)
                
                try:
                    # 解析JSON格式的日志行
                    record = json.loads(line)
                    raw_cmd = record["cmd"].strip()  # 用户执行的命令
                    ts = int(record["ts"])  # 时间戳
                    exit_code = record.get("exit_code", 0)  # 退出码

                    # 修复：清理命令中的历史编号
                    cmd = self._clean_command(raw_cmd)
                    
                    # 跳过空命令、注释命令和失败命令
                    if not cmd or cmd.startswith('#') or exit_code != 0:
                        continue

                    # 修复：处理异常时间戳
                    current_time = int(time.time())
                    if ts > current_time + 3600 or ts < 1600000000:  # 过滤异常时间戳
                        ts = current_time  # 使用当前时间作为替代

                    # 会话切分逻辑：如果距离上次操作超过10分钟，开始新会话
                    if current_session and (ts - last_ts) > 600:
                        if len(current_session) >= 2:  # 只保留有意义的会话
                            sessions.append(current_session)
                        current_session = [cmd]  # 新会话以当前命令开始
                    else:
                        current_session.append(cmd)  # 继续当前会话

                    last_ts = ts  # 更新最后时间戳
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"跳过第 {line_num} 行解析错误: {e}")
                    print(f"问题行内容: {line[:100]}...")  # 显示前100个字符
                    continue

        # 不要忘记添加最后一个会话（只保留有意义的会话）
        if len(current_session) >= 2:
            sessions.append(current_session)
        
        print(f"解析出 {len(sessions)} 个有效会话")
        return sessions

    def _fix_json_line(self, line):
        """尝试修复JSON格式问题"""
        # 修复双引号嵌套问题：{"cmd":"echo "test"", ...} → {"cmd":"echo \"test\"", ...}
        try:
            # 使用不同的方法来修复引号问题
            def replace_quotes(match):
                group1 = match.group(1)  # "cmd":"
                content = match.group(2)  # 命令内容
                group3 = match.group(3)   # ",
                # 将内容中的双引号转义
                fixed_content = content.replace('"', '\\"')
                return group1 + fixed_content + group3
            
            line = re.sub(r'("cmd":")(.*?)(",)', replace_quotes, line)
        except Exception as e:
            print(f"JSON修复失败: {e}")
        return line

    def _clean_command(self, raw_cmd):
        """清理命令：移除历史编号和多余空格"""
        # 移除类似 "825  source ~/.bashrc" 中的数字前缀
        parts = raw_cmd.split()
        if parts and parts[0].isdigit() and len(parts) > 1:
            # 去掉开头的数字，保留剩余部分
            cleaned = ' '.join(parts[1:])
        else:
            cleaned = raw_cmd
        
        # 移除多余空格并返回
        return ' '.join(cleaned.split())

    def _train_on_session(self, session):
        """
        从一个命令会话中提取 n-gram 转移关系
        支持两种上下文长度：
        - 1-gram: 只考虑前一个命令
        - 2-gram: 考虑前两个命令
        """
        print(f"训练会话: {session[:3]}...")  # 显示前3个命令用于调试
        
        # 遍历会话中的每个命令（从第一个到最后一个）
        for i in range(len(session)):
            # 当前要预测的命令（作为下一个命令）
            next_cmd = session[i]
            
            # 1-gram 训练：基于前一个命令预测下一个命令
            if i >= 1:  # 确保有前一个命令
                ctx1 = (session[i-1],)  # 单元素元组作为1-gram上下文
                self.transitions[ctx1][next_cmd] += 1  # 计数增加
            
            # 2-gram 训练：基于前两个命令预测下一个命令
            if i >= 2:  # 确保有前两个命令
                ctx2 = (session[i-2], session[i-1])  # 双元素元组作为2-gram上下文
                self.transitions[ctx2][next_cmd] += 1  # 计数增加

    def predict_next(self, previous_commands, top_k=3):
        """
        根据历史命令预测下一个可能执行的命令
        Args:
            previous_commands: 最近执行的命令列表，如 ['git', 'add']
            top_k: 返回前K个最可能的预测
        Returns:
            最可能的下一个命令列表，如 [('git commit', 5), ('git status', 2)]
        """
        if not previous_commands:
            return []
        
        predictions = []
        
        # 优先使用2-gram上下文（更精确）
        if len(previous_commands) >= 2:
            ctx = tuple(previous_commands[-2:])
            if ctx in self.transitions:
                predictions.extend(self.transitions[ctx].most_common(top_k))
                print(f"使用2-gram上下文 {ctx} 找到 {len(predictions)} 个预测")
        
        # 回退到1-gram上下文
        if len(previous_commands) >= 1 and len(predictions) < top_k:
            ctx = (previous_commands[-1],)
            if ctx in self.transitions:
                remaining = top_k - len(predictions)
                new_predictions = self.transitions[ctx].most_common(remaining)
                predictions.extend(new_predictions)
                print(f"使用1-gram上下文 {ctx} 找到 {len(new_predictions)} 个预测")
        
        # 修复：如果还是没找到，尝试模糊匹配
        if not predictions:
            predictions = self._fuzzy_predict(previous_commands, top_k)
            if predictions:
                print(f"使用模糊匹配找到 {len(predictions)} 个预测")
        
        return predictions[:top_k]

    def _fuzzy_predict(self, context, top_k=3):
        """模糊预测：即使上下文不完全匹配也尝试预测"""
        all_predictions = []
        
        # 收集所有相关的转移
        for ctx, counter in self.transitions.items():
            # 如果上下文的任何部分包含当前命令
            ctx_str = ' '.join(ctx)
            if any(cmd in ctx_str for cmd in context if len(cmd) > 2):
                all_predictions.extend(counter.most_common(3))
        
        # 按频率排序并去重
        unique_predictions = {}
        for cmd, count in all_predictions:
            if cmd not in unique_predictions or count > unique_predictions[cmd]:
                unique_predictions[cmd] = count
        
        sorted_predictions = sorted(unique_predictions.items(), key=lambda x: x[1], reverse=True)
        return sorted_predictions[:top_k]

    def debug_transitions(self):
        """调试函数：显示学到的命令模式"""
        print("\n=== 学到的命令模式 ===")
        for context, counter in list(self.transitions.items())[:10]:  # 显示前10个
            print(f"当输入 {context} 后，可能执行: {counter.most_common(3)}")

    def get_command_stats(self):
        """获取命令统计信息"""
        total_transitions = sum(len(counter) for counter in self.transitions.values())
        print(f"\n=== 模型统计 ===")
        print(f"学习到的上下文模式: {len(self.transitions)} 个")
        print(f"总转移关系: {total_transitions} 个")
        
        # 显示最常用的命令
        all_commands = Counter()
        for counter in self.transitions.values():
            for cmd, count in counter.items():
                all_commands[cmd] += count
        
        print(f"最常用命令: {all_commands.most_common(5)}")


