# PStock 智能体运行指南

## ✅ 成功运行！

您的 PStock 智能体框架已经成功运行！上面您看到的是使用**模拟LLM**的演示结果。

## 📊 运行结果展示

刚才运行的 `financial_analyst` 智能体包含：

- **2个工具**:
  - `stock_data` - 股票数据工具
  - `agent_data_fetcher` - 子智能体工具

- **1个技能**:
  - `market_analysis` - 市场分析技能

- **1个子智能体**:
  - `data_fetcher` - 数据获取子智能体

## 🚀 如何使用真实AI模型

要使用真实的AI模型（如 GPT-4、Claude 等），请按以下步骤操作：

### 方法 1: 使用 .env 文件（推荐）

1. **创建 .env 文件**:
```bash
cat > .env << 'EOF'
# OpenAI API 配置
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# 或使用其他兼容的API
# OPENAI_API_BASE=https://api.deepseek.com/v1
EOF
```

2. **使用 --real-llm 参数运行**:
```bash
python run_agent.py "分析苹果公司股票" --real-llm
```

### 方法 2: 修改脚本直接配置

编辑 `run_agent.py` 文件，在 `create_real_llm()` 函数中直接配置：

```python
def create_real_llm():
    from pstock_sdk import OpenAILLM

    return OpenAILLM(
        api_key="sk-your-api-key-here",
        options={"model": "gpt-4o-mini"},
    )
```

然后在运行脚本时添加 `--real-llm` 参数。

## 📝 运行方式

### 1. 单次运行

```bash
# 基本用法
python run_agent.py "你的任务描述"

# 使用真实AI
python run_agent.py "分析特斯拉股票" --real-llm

# 示例任务
python run_agent.py "比较苹果、微软和谷歌的股票投资价值"
python run_agent.py "分析NVDA的技术指标并给出买卖建议"
python run_agent.py "评估加密货币市场的整体趋势"
```

### 2. 交互式模式

```bash
# 启动交互式模式
python run_agent.py --interactive

# 然后输入你的任务
请输入任务: 分析AAPL股票
请输入任务: 比较TSLA和RIVN
请输入任务: quit  # 退出
```

## 📂 智能体目录结构

```
agents/
└── financial_analyst/          # 金融分析师智能体
    ├── agent.json              # 配置文件
    ├── prompt.md               # 系统提示词
    ├── skills/
    │   └── market_analysis/
    │       └── SKILL.md        # 市场分析技能
    ├── tools/
    │   └── stock_data.py       # 股票数据工具
    └── subagents/
        └── data_fetcher/       # 数据获取子智能体
            └── agent.json
```

## 🛠️ 添加新的智能体

### 1. 创建简单智能体

```bash
# 创建智能体目录
mkdir -p agents/my_agent
cd agents/my_agent

# 创建配置文件
cat > agent.json << 'EOF'
{
  "name": "my_agent",
  "version": "1.0.0",
  "description": "我的自定义智能体",
  "model": null,
  "prompt": {
    "system": "你是一个有用的AI助手。"
  }
}
EOF

# 运行
cd ../..
python run_agent.py "测试我的智能体"
```

### 2. 创建带工具的智能体

```bash
mkdir -p agents/code_analyzer/tools
cd agents/code_analyzer

# 创建配置
cat > agent.json << 'EOF'
{
  "name": "code_analyzer",
  "version": "1.0.0",
  "description": "代码分析智能体",
  "model": null,
  "prompt": {
    "system": "你是一个专业的代码分析助手。"
  },
  "tools": {
    "auto_discover": true
  }
}
EOF

# 创建工具
cat > tools/code_review.py << 'EOF'
from pstock_sdk.agent.tools.base_tool import BaseTool

class CodeReviewTool(BaseTool):
    name = "code_review"
    description = "Review code and provide suggestions"

    async def execute(self, input, context=None):
        code = input.get("code", "")
        return f"Code review for:\n{code}"

tool = CodeReviewTool()
EOF

# 运行
cd ../..
python run_agent.py "分析这段Python代码的质量"
```

## 🔧 自定义和扩展

### 添加真实的数据获取功能

编辑 `agents/financial_analyst/tools/stock_data.py`:

```python
import yfinance as yf

class StockDataTool(BaseTool):
    name = "stock_data"
    description = "获取真实股票数据"

    async def execute(self, input, context=None):
        symbol = input.get("symbol", "AAPL")
        ticker = yf.Ticker(symbol)

        # 获取真实数据
        info = ticker.info
        current_price = info.get('currentPrice')
        market_cap = info.get('marketCap')

        return f"""
股票: {symbol}
当前价格: ${current_price}
市值: ${market_cap:,}
        """
```

### 添加更多技能

创建 `agents/financial_analyst/skills/technical_analysis/SKILL.md`:

```markdown
---
name: technical_analysis
description: 技术分析和图表模式识别
allowed_tools:
  - stock_data
version: "1.0.0"
tags:
  - technical
  - indicators
---

# 技术分析技能

## 移动平均线
- MA50: 50日移动平均线
- MA200: 200日移动平均线

## RSI指标
- 超买区: RSI > 70
- 超卖区: RSI < 30

## MACD
- 分析MACD金叉和死叉信号
```

## 📊 监控和调试

查看详细日志：

```bash
# 设置日志级别为 DEBUG
LOG_LEVEL=DEBUG python run_agent.py "分析任务"
```

## 🎯 常见任务示例

```bash
# 股票分析
python run_agent.py "分析AAPL的基本面和技术面"

# 投资组合分析
python run_agent.py "评估一个由科技股组成的投资组合"

# 市场趋势
python run_agent.py "分析当前美股市场的整体趋势"

# 比较分析
python run_agent.py "比较特斯拉和比亚迪的投资价值"

# 风险评估
python run_agent.py "评估投资NVDA的风险和收益"
```

## 🔐 安全注意事项

1. **不要提交 .env 文件** 到版本控制
2. **保护好你的 API 密钥**
3. **建议使用环境变量**而不是硬编码
4. **设置合理的预算限制**避免意外超支

## 📚 更多资源

- [框架实现总结](FRAMEWORK_SUMMARY.md)
- [智能体创建指南](agents/README.md)
- [PStock SDK 文档](src/pstock_sdk/README.md)

## 🆘 故障排除

### 问题 1: 导入错误
```bash
# 确保在项目根目录运行
cd /home/estom/work/pstock
python run_agent.py "任务"
```

### 问题 2: API 密钥错误
```bash
# 检查 .env 文件是否存在
cat .env

# 确保 API 密钥正确
echo $OPENAI_API_KEY
```

### 问题 3: 智能体加载失败
```bash
# 检查 agent.json 语法
python -m json.tool agents/financial_analyst/agent.json

# 查看详细错误日志
python run_agent.py "任务" 2>&1 | grep ERROR
```

## 🎉 下一步

1. **配置真实API** - 使用 OpenAI 或其他兼容的API
2. **创建自定义工具** - 实现真实的数据获取功能
3. **添加更多智能体** - 构建你自己的智能体生态
4. **优化提示词** - 改进智能体的性能
5. **集成到应用** - 在你的应用中使用这些智能体

---

**祝您使用愉快！** 🚀
