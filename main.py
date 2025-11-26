from model import LocalWorldModel

def main():
    # 初始化模型
    model = LocalWorldModel(log_path="~/.wm_shell/history.jsonl")
    
    # 加载并训练模型
    model.load_and_train()
    
    # 调试输出
    model.debug_transitions()
    
    # 测试预测功能
    test_context = ['cat', '~/.wm_shell/history.jsonl']
    predictions = model.predict_next(test_context, top_k=5)
    print(f"\n在命令 {test_context} 后，可能执行: {predictions}")

if __name__ == "__main__":
    main()