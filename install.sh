#! /bin/bash
# install.sh

CONFIG_DIR="$HOME/.wm_shell"    # 目录
LOG_FILE="$CONFIG_DIR/history.jsonl"    # 日志文件，jsonl格式

# 创建配置目录
mkdir -p $CONFIG_DIR

# shell 配置文件中注入一个函数，用于记录用户在终端中执行的所有命令及其上下文信息。
RECORD_CMD='
wm_shell_log(){
    local CMD="$1"  # 获取执行的命令
    local CWD="$PWD" # 记录当前目录
    local TS=$(date +%s)    # 获取当前时间戳
    local EXIT_CODE="$?"    # 获取命令的退出码

    # 跳过空命令和nxcmd的命令,避免循环记录
    if [[ -n "$CMD" && "$CMD" != *"nxcmd"* && "$CMD" != *"wm_shell_log"* ]]; then
        echo "{\"cmd\":\"$CMD\",\"cwd\":\"$CWD\",\"ts\":\"$TS\",\"exit_code\":$EXIT_CODE}" >> "'"$LOG_FILE"'"
    fi
}
'
# echo "$RECORD_CMD" >> $HOME/.bashrc

if [[ -f "$HOME/.bashrc" ]]; then
    if ! grep -q "wm_shell_log" $HOME/.bashrc; then
        echo "$RECORD_CMD" >> $HOME/.bashrc
        # 设置bash的 PROMPT_COMMAND 来捕获命令
        echo 'export PROMPT_COMMAND="wm_shell_log \"\$(history 1 | sed \"s/^[]*[0-9]*[ ]*//\")\""' >> $HOME/.bashrc
        echo "Added to ~/.bashrc successfully"
    fi
else
    echo "~/.bashrc not found"
fi

# 为 Zsh shell 安装命令记录功能
if [[ -f "$HOME/.zshrc" ]]; then            # 检查是否存在 .zshrc 文件
  if ! grep -q "wm_shell_log" "$HOME/.zshrc"; then   # 检查是否已经安装过
    # 将记录函数注入到 .zshrc
    echo "$RECORD_CMD" >> "$HOME/.zshrc"
    # 使用 Zsh 的 preexec 钩子：在命令执行前记录命令
    echo 'preexec() { wm_shell_log "$1"; }' >> "$HOME/.zshrc"
    echo "Added to ~/.zshrc"   # 提示安装成功
  fi
fi

# 提示用户重新加载 shell 配置以使更改生效
echo "Please run: source ~/.bashrc  or  source ~/.zshrc"