# src/nxcmd/cli.py
import sys
import json
from pathlib import Path
from .model import LocalWorldModel


def get_recent_commands(n=2):
    """从日志末尾读取最近 n 条命令（排除 nextcmd 自身）"""
    log_path = Path("~/.wm_shell/history.jsonl").expanduser()
    if not log_path.exists():
        return []
    
    recent = []
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 从后往前找有效命令
    for line in reversed(lines):
        try:
            record = json.loads(line.strip())
            cmd = record["cmd"].strip()
            # 使用与模型相同的清理逻辑
            cleaned_cmd = clean_command(cmd)
            if cleaned_cmd and "nextcmd" not in cmd and "main.py" not in cmd:
                recent.append(cleaned_cmd)
                if len(recent) >= n:
                    break
        except:
            continue
    
    return list(reversed(recent))  # 保持时间顺序

def clean_command(raw_cmd):
    """清理命令：移除历史编号和多余空格（与模型中的逻辑保持一致）"""
    parts = raw_cmd.split()
    if parts and parts[0].isdigit() and len(parts) > 1:
        cleaned = ' '.join(parts[1:])
    else:
        cleaned = raw_cmd
    return ' '.join(cleaned.split())

def show_help():
    """显示帮助信息"""
    print("""
🔮 NxCmd - 智能命令预测工具

使用方法:
  nxcmd suggest      # 基于最近命令预测下一个可能命令
  nxcmd simulate <cmd>  # 模拟在指定命令后的预测
  nxcmd stats       # 显示模型统计信息
  nxcmd demo        # 运行演示模式
  nxcmd help        # 显示此帮助信息

示例:
  nxcmd suggest
  nxcmd simulate "git add"
  nxcmd stats
    """)

def run_demo(model):
    """演示模式：展示模型功能"""
    print("=== NextCmd 演示模式 ===")
    
    print("\n📊 模型统计信息:")
    model.get_command_stats()
    
    print("\n🎯 学习到的命令模式:")
    model.debug_transitions()
    
    # 测试几个常见的预测场景
    test_cases = [
        ['git', 'add'],
        ['cd', '~'],
        ['ls', '-la']
    ]
    
    print("\n🧪 预测测试:")
    for context in test_cases:
        predictions = model.predict_next(context, top_k=3)
        if predictions:
            print(f"在命令 {' → '.join(context)} 后，可能执行:")
            for cmd, count in predictions:
                print(f"  - {cmd} ({count}次)")
        else:
            print(f"在命令 {' → '.join(context)} 后: 无预测结果")
        print()

def main():
    """CLI 主入口函数"""
    if len(sys.argv) < 2 or sys.argv[1] in ['help', '--help', '-h']:
        show_help()
        return

    # 初始化并训练模型
    model = LocalWorldModel()
    print("🔮 加载命令历史并训练模型...")
    model.load_and_train()

    command = sys.argv[1]

    if command == "suggest":
        recent = get_recent_commands(n=2)
        if not recent:
            print("ℹ️  未找到最近的命令。请先在终端中使用一些命令！")
            print("   尝试使用: ls, cd, git status 等命令，然后再次运行。")
            return

        print(f"🧠 基于最近命令: {' → '.join(recent)}")
        
        # 使用模型的预测方法
        suggestions = model.predict_next(recent, top_k=5)
        
        if suggestions:
            print("💡 建议的下一个命令:")
            for i, (cmd, count) in enumerate(suggestions, 1):
                print(f"  {i}. {cmd} (出现 {count} 次)")
        else:
            print("🤔 未找到建议。尝试使用更多命令来丰富模型！")
            print("   或者使用 'nextcmd simulate <你的命令>' 来测试特定命令")

    elif command == "simulate":
        if len(sys.argv) < 3:
            print("❌ 请提供要模拟的命令")
            print("   例如: nextcmd simulate 'git add'")
            print("   例如: nextcmd simulate 'cd projects' 'ls'")
            sys.exit(1)
        
        # 支持多个上下文命令
        context_commands = []
        for i in range(2, len(sys.argv)):
            cmd = clean_command(sys.argv[i])
            context_commands.append(cmd)
        
        print(f"🔮 模拟命令后: {' → '.join(context_commands)}")
        suggestions = model.predict_next(context_commands, top_k=5)
        
        if suggestions:
            print("💡 常见的后续命令:")
            for i, (cmd, count) in enumerate(suggestions, 1):
                print(f"  {i}. {cmd} (出现 {count} 次)")
        else:
            print("🤔 未找到常见的后续命令。")

    elif command == "stats":
        # 显示模型统计信息
        model.get_command_stats()
        print("\n📊 最近学到的模式:")
        model.debug_transitions()

    elif command == "demo":
        # 运行演示模式
        run_demo(model)

    else:
        print(f"❌ 未知命令: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()