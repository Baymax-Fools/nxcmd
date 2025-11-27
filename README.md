NXCMD - 智能命令预测工具
🔮 NXCMD 是一个基于本地世界模型的智能命令行预测工具，通过学习你的命令历史来预测下一步可能执行的命令。

功能特性

🧠 智能预测: 基于你的命令使用习惯，预测下一个可能执行的命令

📚 本地学习: 所有数据都在本地处理，保护隐私

⚡ 快速响应: 基于轻量级 n-gram 模型，预测速度快

🛠️ 多 Shell 支持: 支持 Bash 和 Zsh

📊 统计展示: 查看模型学习到的命令模式

安装
方法一：使用安装脚本
bash
# 克隆项目
git clone <你的仓库地址>
cd nxcmd

# 运行安装脚本
./install.sh

# 重新加载 Shell 配置
source ~/.bashrc  # 或 source ~/.zshrc
方法二：使用 pip 安装
bash
# 从源码安装
pip install .

# 或者以开发模式安装
pip install -e .
使用方法
安装完成后，直接在终端中使用 nxcmd 命令：

获取建议
bash
# 基于最近命令预测下一个命令
nxcmd suggest
模拟预测
bash
# 模拟在特定命令后的预测
nxcmd simulate "git add"
nxcmd simulate "cd projects" "ls"
查看统计
bash
# 显示模型统计信息和学习到的模式
nxcmd stats
演示模式
bash
# 运行演示，展示模型功能
nxcmd demo
获取帮助
bash
nxcmd help
工作原理
NXCMD 通过分析你的命令历史记录，构建一个本地世界模型：

数据收集: 自动记录你在终端中执行的命令（排除 nxcmd 自身）

会话分割: 根据时间间隔（10分钟）将命令分割为独立会话

模式学习: 使用 n-gram 模型学习命令序列模式

1-gram: 基于前一个命令预测

2-gram: 基于前两个命令预测

智能预测: 根据当前上下文提供最可能的命令建议

开发
环境要求
Python >= 3.8

Bash 或 Zsh

本地开发
bash
# 克隆项目
git clone <仓库地址>
cd nxcmd

# 以开发模式安装
pip install -e .

# 运行测试
python -m pytest tests/
数据隐私
NXCMD 完全在本地运行：

✅ 所有命令历史存储在 ~/.wm_shell/history.jsonl

✅ 所有模型训练在本地完成

✅ 无数据上传到云端

✅ 你可以随时删除历史数据

故障排除
命令记录不工作
确保已重新加载 Shell 配置：

bash
source ~/.bashrc  # 或 source ~/.zshrc
没有预测结果
确保先使用一些常用命令：

bash
cd ~
ls -la
git status
查看日志文件
bash
cat ~/.wm_shell/history.jsonl
许可证
MIT License

贡献
欢迎提交 Issue 和 Pull Request！

NXCMD - 让你的命令行更智能！ 🚀
