# nextcmd/model.py
import json
from pathlib import Path
from collections import defaultdict, Counter
import time

class LocalWorldModel:
    def __init__(self, log_path="~/.wm_shell/history.jsonl"):
        self.log_path = Path(log_path).expanduser()
        self.transitions = defaultdict(Counter)

    def load_and_train(self):
        """从日志加载数据并训练 n-gram 模型"""
        sessions = self._parse_logs_into_sessions()
        for session in sessions:
            self._train_on_session(session)
        print(f"训练完成，学习了 {len(self.transitions)} 个命令模式")

    def _parse_logs_into_sessions(self):
        """将日志按会话切分（10分钟以上无操作视为新会话）"""
        if not self.log_path.exists():
            print("日志文件不存在，跳过训练")
            return []
        
        sessions = []
        current_session = []
        last_ts = 0

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line.strip())
                    raw_cmd = record["cmd"].strip()
                    ts = int(record["ts"])
                    exit_code = record.get("exit_code", 0)

                    # 🔴 修复1: 清理命令中的历史编号
                    cmd = self._clean_command(raw_cmd)
                    
                    # 跳过无效命令
                    if not cmd or cmd.startswith('#') or exit_code != 0:
                        continue

                    # 🔴 修复2: 处理异常时间戳
                    current_time = int(time.time())
                    if ts > current_time + 3600 or ts < 1600000000:  # 过滤异常时间戳
                        ts = current_time  # 使用当前时间作为替代

                    # 会话切分逻辑
                    if current_session and (ts - last_ts) > 600:
                        if len(current_session) >= 2:  # 只保留有意义的会话
                            sessions.append(current_session)
                        current_session = [cmd]
                    else:
                        current_session.append(cmd)

                    last_ts = ts
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"跳过第 {line_num} 行解析错误: {e}")
                    continue

        if len(current_session) >= 2:
            sessions.append(current_session)
        
        print(f"解析出 {len(sessions)} 个有效会话")
        return sessions

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
        """从一个会话中提取 n-gram 转移"""
        print(f"训练会话: {session[:3]}...")  # 显示前3个命令用于调试
        
        for i in range(len(session)):
            next_cmd = session[i]
            
            # 1-gram: 基于前一个命令
            if i >= 1:
                ctx1 = (session[i-1],)
                self.transitions[ctx1][next_cmd] += 1
            
            # 2-gram: 基于前两个命令
            if i >= 2:
                ctx2 = (session[i-2], session[i-1])
                self.transitions[ctx2][next_cmd] += 1

    def predict_next(self, previous_commands, top_k=3):
        """根据历史命令预测下一个可能执行的命令"""
        predictions = []
        
        # 优先使用2-gram
        if len(previous_commands) >= 2:
            ctx = tuple(previous_commands[-2:])
            if ctx in self.transitions:
                predictions.extend(self.transitions[ctx].most_common(top_k))
        
        # 回退到1-gram
        if len(previous_commands) >= 1 and len(predictions) < top_k:
            ctx = (previous_commands[-1],)
            if ctx in self.transitions:
                remaining = top_k - len(predictions)
                predictions.extend(self.transitions[ctx].most_common(remaining))
        
        return predictions[:top_k]

    def debug_transitions(self):
        """调试函数：显示学到的命令模式"""
        for context, counter in list(self.transitions.items())[:10]:  # 显示前10个
            print(f"当输入 {context} 后，可能执行: {counter.most_common(3)}")

# 测试代码
if __name__ == "__main__":
    model = LocalWorldModel()
    model.load_and_train()
    model.debug_transitions()
    
    # 测试预测
    test_context = ['cat', '~/.wm_shell/history.jsonl']
    predictions = model.predict_next(test_context)
    print(f"\n在命令 {test_context} 后，可能执行: {predictions}")