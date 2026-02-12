# 🎉 PStock Framework智能体框架 - 运行成功！

## ✅ 当前状态

您的 **PStock 智能体框架**已经成功实现并运行！

### 📦 已完成的组件

✅ **pstock_framework** - 声明式智能体框架
✅ **工具系统** - 自动发现和加载
✅ **技能系统** - Claude Skills 支持
✅ **子智能体** - 递归加载和协作
✅ **运行脚本** - 便捷的启动器

## 🚀 快速开始

### 方法 1: 使用启动脚本（推荐）

```bash
python /src/agents/financial_analyst/agent.py
```

然后选择你想要的运行模式。

### 方法 2: 直接运行

```bash
# 单次运行
python agent.py "分析苹果公司股票"
```

## 📊 运行示例

### 示例 1: 股票分析

```bash
python /src/agents/financial_analyst/agent.py
```

## 🎯 当前可用的智能体

### financial_analyst（金融分析师）

**功能**:
- 📈 股票价格查询
- 📊 技术指标分析
- 💼 基本面分析
- 🔍 市场趋势判断
- 🎯 投资建议

**工具**:
- `stock_data` - 股票数据工具
- `agent_data_fetcher` - 数据获取子智能体

**技能**:
- `market_analysis` - 高级市场分析技术

**子智能体**:
- `data_fetcher` - 专业的数据获取智能体

## 🔧 配置真实AI

### 创建 .env 文件

```bash
cat > .env << 'EOF'
# OpenAI API
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# 或使用其他兼容API
# OPENAI_API_BASE=https://api.deepseek.com/v1
EOF
```

### 使用真实AI运行

```bash
python run_agent.py "分析任务" --real-llm
```

## 📁 项目结构

```
pstock/
├── src/
│   ├── pstock_framework/     # ✨ 声明式框架
│   └── pstock_sdk/          # 🛠️ SDK 核心
```

## 🎨 创建自己的智能体

### 快速创建一个简单智能体

```bash
# 1. 创建目录
mkdir -p agents/my_agent

# 2. 创建配置
cat > agents/my_agent/agent.json << 'EOF'
{
  "name": "my_agent",
  "version": "1.0.0",
  "description": "我的智能体",
  "model": null,
  "prompt": {
    "system": "你是一个有用的AI助手。"
  }
}
EOF

# 3. 运行
python run_agent.py "测试我的智能体"
```

详细指南请查看: [agents/README.md](agents/README.md)

## 🔥 核心功能

### 1. 声明式配置

使用 JSON 文件配置智能体，无需编码：

```json
{
  "name": "my_agent",
  "description": "智能体描述",
  "model": {"model": "gpt-4"},
  "prompt": {"system": "系统提示词"},
  "tools": {"auto_discover": true},
  "skills": {"sources": ["skills/"]},
  "subagents": [
    {"name": "child_agent", "enabled": true}
  ]
}
```

### 2. 工具自动发现

在 `tools/` 目录放置 Python 文件即可：

```python
# tools/my_tool.py
from pstock_sdk.agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "工具描述"

    async def execute(self, input, context=None):
        return "执行结果"

tool = MyTool()  # 框架会自动发现
```

### 3. Claude Skills 支持

使用标准 Claude Skills 格式：

```markdown
---
name: my_skill
description: 技能描述
allowed_tools:
  - tool1
  - tool2
---

# 技能说明

详细的使用说明...
```

### 4. 子智能体协作

智能体可以调用其他智能体：

```json
{
  "subagents": [
    {
      "name": "data_fetcher",
      "alias": "fetch_data",
      "enabled": true
    }
  ]
}
```

## 📊 性能特点

- ⚡ **快速加载**: 毫秒级智能体加载
- 🔄 **自动发现**: 零配置工具和技能加载
- 🛡️ **错误容错**: 单个工具失败不影响整体
- 🔁 **循环检测**: 自动防止子智能体循环引用
- 💾 **配置缓存**: 高效的配置管理

## 🧪 测试

```bash
# 运行框架测试
python test_framework.py

# 测试特定智能体
python run_agent.py "测试任务"
```

## 📚 文档

- **[框架实现总结](FRAMEWORK_SUMMARY.md)** - 完整的技术实现细节
- **[运行指南](AGENT_RUNNER_GUIDE.md)** - 详细的使用说明
- **[智能体创建指南](agents/README.md)** - 如何创建新智能体
- **[API 文档](src/pstock_sdk/README.md)** - SDK API 参考

## 🎯 下一步

1. **配置真实API** - 体验完整AI能力
2. **创建自定义工具** - 实现真实数据获取
3. **添加更多智能体** - 构建智能体生态
4. **优化提示词** - 提升智能体性能
5. **集成到应用** - 在实际场景中使用

## 💡 使用示例

### 场景 1: 股票分析助手

```bash
python run_agent.py "作为专业的股票分析师，请分析以下方面：
1. 苹果公司当前的基本面状况
2. 技术指标显示的买入/卖出信号
3. 未来12个月的价格预期
4. 主要风险因素
请给出具体的投资建议。"
```

### 场景 2: 投资组合优化

```bash
python run_agent.py "我有一个投资组合：
- 40% 科技股（AAPL, MSFT, GOOGL）
- 30% 金融股（JPM, BAC）
- 20% 医疗股（JNJ, PFE）
- 10% 现金

请分析这个配置是否合理，并给出优化建议。"
```

### 场景 3: 市场研究

```bash
python run_agent.py "研究当前的半导体行业趋势，包括：
1. 行业整体前景
2. 主要公司对比（NVDA, AMD, INTC）
3. 潜在的投资机会
4. 需要注意的风险"
```

## 🆘 获取帮助

- 查看文档: `cat AGENT_RUNNER_GUIDE.md`
- 运行测试: `python test_framework.py`
- 查看示例: `ls agents/financial_analyst/`
- 交互模式: `python run_agent.py --interactive`

## 🎊 总结

你现在拥有：

✅ **完整的智能体框架** - 声明式配置，自动加载
✅ **可运行的示例智能体** - 金融分析师
✅ **便捷的运行工具** - 一键启动
✅ **完善的文档** - 从入门到精通
✅ **扩展性强** - 轻松添加新功能

**开始探索吧！** 🚀

---

*PStock Framework v0.1.0* | *Generated 2026-02-02*
