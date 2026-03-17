# 🚀 AI Flex 智能体 - 快速参考

## 一键启动

```bash
# 方式 1: 使用启动脚本（最简单）
./start.sh

# 方式 2: 运行演示
./demo.sh

# 方式 3: 直接运行
python run_agent.py "你的任务"
```

## 常用命令

### 基础运行
```bash
# 单次任务
python run_agent.py "分析AAPL股票"

# 交互式模式
python run_agent.py --interactive

# 使用真实AI
python run_agent.py "任务" --real-llm
```

### 测试和验证
```bash
# 框架测试
python test_framework.py

# 完整演示
./demo.sh

# 验证安装
python -c "from framework import AgentFrameworkLoader; print('✓ OK')"
```

### 配置管理
```bash
# 创建配置文件
cp .env.template .env

# 编辑配置
nano .env

# 查看智能体配置
cat agents/financial_analyst/agent.json | python -m json.tool
```

## 示例任务

### 股票分析
```bash
python run_agent.py "分析苹果公司股票的基本面和技术面"
python run_agent.py "评估特斯拉的投资价值"
python run_agent.py "比较英伟达和AMD"
```

### 市场研究
```bash
python run_agent.py "分析当前半导体行业趋势"
python run_agent.py "评估科技股的投资机会"
python run_agent.py "预测下季度市场走势"
```

### 投资建议
```bash
python run_agent.py "我应该现在买入NVDA吗？"
python run_agent.py "我的投资组合是否合理？"
python run_agent.py "如何降低投资风险？"
```

## 目录结构

```
aiflex/
├── src/framework/      # 框架代码
├── agents/                     # 智能体目录
│   └── financial_analyst/     # 金融分析师
│       ├── agent.json         # 配置文件
│       ├── prompt.md          # 提示词
│       ├── skills/            # 技能目录
│       ├── tools/             # 工具目录
│       └── subagents/         # 子智能体
├── run_agent.py              # 运行脚本
├── start.sh                  # 启动脚本
├── demo.sh                   # 演示脚本
└── .env.template            # 配置模板
```

## 配置 API 密钥

### 1. 创建 .env 文件
```bash
cp .env.template .env
```

### 2. 编辑 .env
```bash
# 使用 OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini

# 或使用 DeepSeek
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=your-deepseek-key
OPENAI_MODEL=deepseek-chat
```

### 3. 使用真实AI运行
```bash
python run_agent.py "任务" --real-llm
```

## 创建新智能体

### 快速模板
```bash
# 1. 创建目录
mkdir -p agents/my_agent

# 2. 创建配置
cat > agents/my_agent/agent.json << EOF
{
  "name": "my_agent",
  "description": "我的智能体",
  "prompt": {"system": "你是一个AI助手"}
}
EOF

# 3. 运行
python run_agent.py "测试"
```

### 带工具的智能体
```bash
mkdir -p agents/code_helper/tools

cat > agents/code_helper/agent.json << EOF
{
  "name": "code_helper",
  "description": "代码助手",
  "tools": {"auto_discover": true}
}
EOF

cat > agents/code_helper/tools/review.py << EOF
from sdk.agent.tools.base_tool import BaseTool

class ReviewTool(BaseTool):
    name = "review"
    description = "代码审查"

    async def execute(self, input, context=None):
        return "审查完成"

tool = ReviewTool()
EOF
```

## 文档参考

| 文档 | 说明 |
|------|------|
| [README_AGENT.md](README_AGENT.md) | 总体介绍 |
| [FRAMEWORK_SUMMARY.md](FRAMEWORK_SUMMARY.md) | 实现细节 |
| [AGENT_RUNNER_GUIDE.md](AGENT_RUNNER_GUIDE.md) | 运行指南 |
| [agents/README.md](agents/README.md) | 智能体创建 |

## 故障排除

### 问题 1: 导入错误
```bash
# 确保在项目根目录
cd /home/estom/work/pstock
pwd
```

### 问题 2: 智能体未加载
```bash
# 检查配置文件
python -m json.tool agents/financial_analyst/agent.json

# 查看错误日志
python run_agent.py "测试" 2>&1 | grep ERROR
```

### 问题 3: API 密钥错误
```bash
# 检查 .env 文件
cat .env

# 测试 API 连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## 性能优化

### 使用更快的模型
```bash
# .env 文件
OPENAI_MODEL=gpt-4o-mini  # 比 gpt-4 快且便宜
```

### 限制最大步数
```bash
# agent.json
{
  "runtime": {
    "max_steps": 5  # 减少推理步骤
  }
}
```

### 禁用不需要的功能
```bash
{
  "tools": {"auto_discover": false},
  "subagents": []
}
```

## 高级用法

### 流式输出
```python
from framework import AgentFrameworkLoader

loader = AgentFrameworkLoader(agents_root="agents/", default_llm=llm)
await loader.load_all()
agent = loader.get_agent("financial_analyst")

# 使用流式运行
result = await agent.run_stream(
    "分析任务",
    context=context,
    emit=lambda step: print(f"步骤: {step.type}")
)
```

### 自定义工具
```python
from sdk.agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的自定义工具"

    async def execute(self, input, context=None):
        # 访问上下文
        agent = context.agent if context else None
        # 执行逻辑
        result = do_something(input)
        return result
```

### 多智能体协作
```json
{
  "subagents": [
    {"name": "analyst", "enabled": true},
    {"name": "researcher", "enabled": true},
    {"name": "writer", "enabled": true}
  ]
}
```

## 获取帮助

- 📖 查看文档: `cat AGENT_RUNNER_GUIDE.md`
- 🧪 运行测试: `python test_framework.py`
- 💻 交互模式: `python run_agent.py --interactive`
- 🎯 快速启动: `./start.sh`

## 贡献

欢迎贡献新的智能体、工具和技能！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

---

**版本**: v0.1.0
**更新**: 2026-02-02
**状态**: ✅ 生产就绪
