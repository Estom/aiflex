# StockTrader 股票交易员智能体设计文档

**版本**: 2.0.0
**创建日期**: 2025-01-15
**更新日期**: 2026-02-12
**作者**: PStock Team
**状态**: 设计阶段（编程式构建）

---

## 目录

1. [概述与架构设计](#1-概述与架构设计)
2. [AgentBuilder 构建模式](#2-agentbuilder-构建模式)
3. [子智能体详细设计](#3-子智能体详细设计)
4. [数据流与接口设计](#4-数据流与接口设计)
5. [实现计划与目录结构](#5-实现计划与目录结构)
6. [使用方式](#6-使用方式)

---

## 1. 概述与架构设计

### 1.1 项目概述

**StockTrader** 是一个基于 PStock 框架的股票研究分析智能体系统。该系统采用多智能体协作架构，通过子智能体分工协作实现全自动化的股票分析流程。系统专注于研究和分析，不涉及实盘交易操作，输出结构化的文本分析报告。

### 1.2 需求分析

| 需求维度 | 说明 |
|---------|------|
| **目标类型** | 研究分析型 - 市场分析、股票研究、投资报告生成 |
| **分析维度** | 技术分析、基本面分析、市场情绪、宏观环境 |
| **策略生成** | 基于分析结果和持仓数据生成具体交易策略 |
| **工作模式** | 全自动流水线 - 用户输入股票代码，自动完成全流程 |
| **输出格式** | 文本报告 - 结构化分析报告 + 交易策略 |

### 1.3 架构设计原则

- **分层解耦**：按处理阶段（数据获取→分析处理→策略生成→报告生成）拆分子智能体，职责清晰
- **可扩展性**：新的分析维度、数据源可通过添加 Skills/Tools 无缝扩展
- **自动化**：用户仅需输入股票代码，系统自动完成全流程分析
- **可复用**：各子智能体独立运行，可被其他智能体复用

### 1.4 系统架构图

```
                    ┌─────────────────────────────────────────┐
                    │           StockTrader (主智能体)          │
                    │  - 接收用户任务 (股票代码/分析请求)         │
                    │  - 协调子智能体执行流水线                  │
                    │  - 汇总分析结果生成最终报告                │
                    └─────────────────────────────────────────┘
                                     │
     ┌───────────────────────────────┼───────────────────────────────┐
     ▼                               ▼                               ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ DataFetcher  │───>│   Analyzer   │───>│  StrategyGen  │───>│   Reporter    │
│  (数据获取)   │    │  (分析处理)   │    │  (策略生成)   │    │  (报告生成)   │
├──────────────┤    ├──────────────┤    ├──────────────┤    ├──────────────┤
│ 股价数据获取  │    │ 技术分析      │    │ 持仓数据获取  │    │ 报告模板应用  │
│ 财务数据获取  │    │ 基本面分析    │    │ 交易信号计算  │    │ 结论汇总整理  │
│ 市场情绪获取  │    │ 市场情绪分析  │    │ 风控检查      │    │ 格式化输出    │
│ 宏观数据获取  │    │ 宏观环境分析  │    │ 策略生成      │    │ 风险评级生成  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                               ▲
                                               │
                                      ┌────────┴────────┐
                                      │   券商API       │
                                      │  (持仓数据)      │
                                      └─────────────────┘
```

### 1.5 设计决策记录

| 决策点 | 选择方案 | 理由 |
|-------|---------|------|
| 配置方式 | **编程式构建 (agent.py)** | 完整类型提示、动态配置、易于调试 |
| 子智能体划分 | 按处理阶段拆分 | 职责清晰，数据流向明确，便于并行优化 |
| 分析能力实现 | Skills + Tools | Skills提供领域知识，Tools提供计算能力 |
| 策略生成 | 独立子智能体 | 与分析解耦，便于接入不同券商API |
| 持仓数据 | 券商API集成 | 实时准确，支持实盘风控 |
| 报告格式 | 纯文本 | 易于集成，便于下游系统消费 |

---

## 2. AgentBuilder 构建模式

### 2.1 核心构建 API

每个智能体通过 `AgentBuilder` 编程式构建，提供流畅的链式 API：

```python
from pstock_sdk import AgentBuilder, OpenAILLM

# 初始化 LLM
llm = OpenAILLM(api_key="sk-xxx", options={"model": "gpt-4o"})

# 构建智能体
agent = (AgentBuilder()
    .with_name("agent_name")
    .with_description("智能体描述")
    .with_instructions("系统提示词")
    .with_max_steps(5)
    .with_tools([tool1, tool2])
    .with_skill_sources(["skills/"])
    .with_children([child_agent])
    .build())
```

### 2.2 工厂函数模式

每个子智能体提供独立的 `create()` 工厂函数：

```python
# subagents/data_fetcher/agent.py

def create(llm: LLM) -> Agent:
    """创建 DataFetcher 子智能体"""
    return (AgentBuilder()
        .with_name("data_fetcher")
        .with_description("专业金融数据获取智能体")
        .with_instructions(_load_instructions())
        .with_max_steps(3)
        .with_tools(_create_tools())
        .with_skill_sources(["skills/"])
        .build())
```

### 2.3 提示词加载

支持从文件加载或内联定义：

```python
def _load_instructions() -> str:
    """加载系统提示词"""
    prompt_path = Path(__file__).parent / "prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    # 默认提示词（内联）
    return """你是数据获取专家..."""
```

---

## 3. 子智能体详细设计

### 3.1 DataFetcher（数据获取子智能体）

#### 职责
负责从各类数据源获取原始数据，为后续分析提供数据基础。

#### 完整实现

```python
# subagents/data_fetcher/agent.py

from pathlib import Path
from pstock_sdk import Agent, AgentBuilder, LLM
from .tools import (
    stock_price_tool,
    financial_data_tool,
    sentiment_tool,
    macro_data_tool,
)


def create(llm: LLM) -> Agent:
    """创建 DataFetcher 子智能体"""
    return (AgentBuilder()
        .with_name("data_fetcher")
        .with_description("专业金融数据获取智能体，支持股价、财务、舆情、宏观数据")
        .with_instructions(_load_instructions())
        .with_max_steps(3)
        .with_tools([
            stock_price_tool,
            financial_data_tool,
            sentiment_tool,
            macro_data_tool,
        ])
        .with_skill_sources([
            str(Path(__file__).parent / "skills")
        ])
        .build())


def _load_instructions() -> str:
    """加载系统提示词"""
    prompt_path = Path(__file__).parent / "prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    return """你是数据获取专家，负责准确高效地获取各类金融数据。

## 工作流程

1. 根据用户请求确定需要的数据类型
2. 调用相应的工具获取数据
3. 进行基础质量校验
4. 返回结构化的数据结果

## 可用工具

- stock_price: 获取实时/历史股价数据 (OHLCV)
- financial_data: 获取财务报表数据 (PE/PB/ROE等)
- sentiment: 获取市场情绪数据 (资金流向/舆情)
- macro_data: 获取宏观经济指标 (利率/通胀等)

## 重要原则

- 数据准确性优先，必要时进行重试
- 缺失数据要明确标注，不要虚构
- 保持数据格式一致性，便于下游处理
"""
```

#### Tools 配置

| 工具名称 | 功能描述 | 输入 | 输出 |
|---------|---------|------|------|
| `stock_price` | 获取实时/历史股价数据 | symbol, period, range | OHLCV数据 |
| `financial_data` | 获取财务报表数据 | symbol, report_type, quarters | 财务指标 |
| `sentiment` | 获取市场情绪数据 | symbol, source | 情绪指标 |
| `macro_data` | 获取宏观经济指标 | indicator, date_range | 宏观数据 |

#### Skills 配置
- `data_quality`: 数据校验、缺失值处理、异常值检测

---

### 3.2 Analyzer（分析处理子智能体）

#### 职责
基于获取的数据进行多维度分析，是核心分析引擎。

#### 完整实现

```python
# subagents/analyzer/agent.py

from pathlib import Path
from pstock_sdk import Agent, AgentBuilder, LLM
from .tools import indicators_tool


def create(llm: LLM) -> Agent:
    """创建 Analyzer 子智能体"""
    return (AgentBuilder()
        .with_name("analyzer")
        .with_description("多维度股票分析引擎，覆盖技术面、基本面、情绪面、宏观面")
        .with_instructions(_load_instructions())
        .with_max_steps(8)
        .with_tools([indicators_tool])
        .with_skill_sources([
            str(Path(__file__).parent / "skills" / "technical"),
            str(Path(__file__).parent / "skills" / "fundamental"),
            str(Path(__file__).parent / "skills" / "sentiment"),
            str(Path(__file__).parent / "skills" / "macro"),
        ])
        .with_memory_enabled(True)
        .build())
```

#### Skills 配置

| 技能名称 | 分析内容 | 核心方法 |
|---------|---------|---------|
| `technical` | 技术分析 | MA/EMA/MACD/RSI/KDJ/布林带/成交量 |
| `fundamental` | 基本面分析 | PE/PB/ROE/DCF估值/财务健康度/行业对比 |
| `sentiment` | 市场情绪 | 资金流向/舆情评分/分析师评级变化 |
| `macro` | 宏观环境 | 利率/通胀/政策影响/行业周期 |

#### Tools 配置
- `indicators`: 技术指标计算库（TA-Lib集成）

#### 工作流程
1. 接收 DataFetcher 传递的数据
2. 依次激活四个 Skills 进行分析
3. 生成结构化分析结论（JSON格式）

---

### 3.3 StrategyGenerator（策略生成子智能体）

#### 职责
基于分析结果和当前持仓数据，生成具体交易策略，包含风控检查。

#### 核心功能
1. **持仓数据获取**：通过券商API获取当前账户持仓
2. **策略生成**：结合分析结论生成具体交易信号（买入/加仓/减仓/清仓）
3. **风控检查**：单股上限、总体仓位控制（软性提醒）
4. **组合影响评估**：计算交易对整体组合的影响

#### 完整实现

```python
# subagents/strategy_generator/agent.py

from pathlib import Path
from pstock_sdk import Agent, AgentBuilder, LLM
from .tools import (
    get_positions_tool,
    risk_check_tool,
    calc_signals_tool,
)


def create(llm: LLM) -> Agent:
    """创建 StrategyGenerator 子智能体"""
    return (AgentBuilder()
        .with_name("strategy_generator")
        .with_description("基于分析结果和持仓数据生成具体交易策略，包含风控检查")
        .with_instructions(_load_instructions())
        .with_max_steps(6)
        .with_tools([
            get_positions_tool,
            risk_check_tool,
            calc_signals_tool,
        ])
        .with_skill_sources([
            str(Path(__file__).parent / "skills" / "position_sizing"),
            str(Path(__file__).parent / "skills" / "entry_strategy"),
            str(Path(__file__).parent / "skills" / "exit_strategy"),
            str(Path(__file__).parent / "skills" / "portfolio_mgmt"),
        ])
        .with_memory_enabled(True)
        .build())
```

#### Tools 配置

| 工具名称 | 功能描述 | 输入 | 输出 |
|---------|---------|------|------|
| `get_positions` | 获取当前持仓 | broker, account_id | 持仓列表 |
| `risk_check` | 风控检查 | positions, new_strategy | 风险报告 |
| `calc_signals` | 计算交易信号 | analysis, positions | 交易信号 |

#### Skills 配置

| 技能名称 | 功能 |
|---------|------|
| `position_sizing` | 仓位管理：凯利公式、固定比例、ATR波动率 |
| `entry_strategy` | 入场策略：突破入场、回调入场、分批建仓 |
| `exit_strategy` | 出场策略：止损止盈、移动止损、时间止损 |
| `portfolio_mgmt` | 组合管理：相关性分析、集中度控制 |

---

### 3.4 Reporter（报告生成子智能体）

#### 职责
将分析结果和策略转化为用户友好的文本报告。

#### 完整实现

```python
# subagents/reporter/agent.py

from pathlib import Path
from pstock_sdk import Agent, AgentBuilder, LLM
from .tools import format_tool


def create(llm: LLM) -> Agent:
    """创建 Reporter 子智能体"""
    return (AgentBuilder()
        .with_name("reporter")
        .with_description("分析报告生成智能体，结构化输出专业投资报告")
        .with_instructions(_load_instructions())
        .with_max_steps(3)
        .with_tools([format_tool])
        .with_skill_sources([
            str(Path(__file__).parent / "skills" / "report_template")
        ])
        .build())
```

#### 输出报告结构

```
=== [股票代码] 综合分析报告 ===

一、核心结论
   - 投资评级: 买入/持有/卖出/观望
   - 目标价位: XXX
   - 风险等级: 低/中/高

二、技术分析
   - 趋势判断: ...
   - 关键点位: ...

三、基本面分析
   - 估值分析: ...
   - 财务健康: ...

四、市场情绪
   - 资金流向: ...
   - 舆情监控: ...

五、宏观环境
   - 行业周期: ...
   - 政策影响: ...

六、交易策略
   操作建议: [加仓]
   建议数量: 50股
   目标价位: $175.00
   止损价位: $168.00
   止盈价位: $195.00

   风控提醒:
   - 单股权重将达14.2%，略超10%上限

七、风险提示
   - 主要风险点
```

---

## 4. 数据流与接口设计

### 4.1 智能体间通信协议

子智能体之间通过 PStock 的 `AgentAdapterTool` 进行调用，数据传递采用标准化 JSON 格式。

#### DataFetcher → Analyzer 数据格式

```json
{
  "symbol": "AAPL",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "price": {
      "current": 178.50,
      "change": 2.35,
      "change_percent": 1.33,
      "ohlcv": [...]
    },
    "financial": {
      "pe": 28.5,
      "pb": 45.2,
      "roe": 0.156
    },
    "sentiment": {
      "score": 0.72,
      "analyst_rating": "buy"
    },
    "macro": {
      "rate": 5.25,
      "inflation": 3.2
    }
  }
}
```

#### Analyzer → StrategyGenerator 数据格式

```json
{
  "symbol": "AAPL",
  "analyses": {
    "technical": {
      "trend": "bullish",
      "support": 172.50,
      "resistance": 185.00,
      "conclusion": "上升趋势延续，建议回调买入"
    },
    "fundamental": {
      "valuation": "fair",
      "target_price": 195.00,
      "conclusion": "基本面稳健，长期持有价值较高"
    },
    "sentiment": {
      "overall": "positive",
      "conclusion": "市场情绪积极，资金持续流入"
    },
    "macro": {
      "impact": "positive",
      "conclusion": "宏观环境整体利好，需关注利率变化"
    }
  }
}
```

#### StrategyGenerator → Reporter 数据格式

```json
{
  "symbol": "AAPL",
  "strategy": {
    "action": "BUY",
    "action_cn": "加仓",
    "quantity": 50,
    "target_price": 175.00,
    "stop_loss": 168.00,
    "take_profit": 195.00,
    "reasoning": "技术面上升趋势延续，基本面稳健"
  },
  "risk_alerts": [
    "单股权重将达14.2%，略超10%上限"
  ],
  "portfolio_impact": {
    "current_weight": 8.2,
    "new_weight": 14.2,
    "cash_after": 32750.00
  }
}
```

### 4.2 主智能体协调流程

```
┌─────────────────────────────────────────────────────────────────┐
│  StockTrader 主智能体 ReAct 循环                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  用户输入: "分析 AAPL"                                           │
│       ↓                                                          │
│  Thought: 需要先获取数据，调用 data_fetcher                      │
│  Action:   call data_fetcher(symbol="AAPL")                      │
│  Observation: { "data": {...} }                                 │
│       ↓                                                          │
│  Thought: 数据已获取，调用 analyzer 进行分析                      │
│  Action:   call analyzer(data={...})                             │
│  Observation: { "analyses": {...} }                              │
│       ↓                                                          │
│  Thought: 分析完成，调用 strategy_generator 生成策略              │
│  Action:   call strategy_generator(analyses={...})               │
│  Observation: { "strategy": {...}, "risk_alerts": [...] }        │
│       ↓                                                          │
│  Thought: 策略已生成，调用 reporter 生成报告                       │
│  Action:   call reporter(analyses={...}, strategy={...})        │
│  Observation: "=== AAPL 综合分析报告 ===\n..."                    │
│       ↓                                                          │
│  Thought: 报告已生成，可以返回最终结果                            │
│  Final Answer: [完整报告内容]                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 错误处理策略

| 错误场景 | 处理方式 | 降级方案 |
|---------|---------|---------|
| 数据源超时 | 重试3次，指数退避 | 使用缓存数据或标记数据不可用 |
| 数据异常/缺失 | 触发 data_quality Skill 校验 | 跳过该维度，继续其他分析 |
| 分析失败 | 记录详细错误日志 | 返回简化结论，标注不确定性 |
| 券商API超时 | 重试2次，使用上次持仓 | 使用虚拟持仓数据继续 |
| 风控超限 | 记录警告，继续生成策略 | 在报告中醒目提示风险 |
| 子智能体不可用 | 自动降级到 Skills 模式 | 主智能体直接调用 Skills |

---

## 5. 实现计划与目录结构

### 5.1 完整目录结构

```
src/pstock_agent/stock_trader/
├── __init__.py                     # 包入口，导出 create_stock_trader()
├── agent.py                        # 主智能体定义
├── prompt.md                       # 主智能体系统提示
├── README.md                       # 使用说明
│
├── subagents/
│   ├── __init__.py                 # 子智能体工厂模块
│   │
│   ├── data_fetcher/               # 数据获取子智能体
│   │   ├── __init__.py             # 导出 create()
│   │   ├── agent.py                # 智能体定义 (AgentBuilder)
│   │   ├── prompt.md                # 系统提示词
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── stock_price.py
│   │   │   ├── financial_data.py
│   │   │   ├── sentiment.py
│   │   │   └── macro_data.py
│   │   └── skills/
│   │       └── data_quality/
│   │           └── SKILL.md
│   │
│   ├── analyzer/                   # 分析处理子智能体
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompt.md
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── indicators.py
│   │   └── skills/
│   │       ├── technical/
│   │       ├── fundamental/
│   │       ├── sentiment/
│   │       └── macro/
│   │
│   ├── strategy_generator/         # 策略生成子智能体
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompt.md
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── get_positions.py
│   │   │   ├── risk_check.py
│   │   │   └── calc_signals.py
│   │   └── skills/
│   │       ├── position_sizing/
│   │       ├── entry_strategy/
│   │       ├── exit_strategy/
│   │       └── portfolio_mgmt/
│   │
│   └── reporter/                   # 报告生成子智能体
│       ├── __init__.py
│       ├── agent.py
│       ├── prompt.md
│       ├── tools/
│       │   ├── __init__.py
│       │   └── format.py
│       └── skills/
│           └── report_template/
│
├── tools/                          # 主智能体工具 (可选)
│   ├── __init__.py
│   └── portfolio.py
│
└── tests/
    ├── test_data_fetcher.py
    ├── test_analyzer.py
    ├── test_strategy_generator.py
    └── test_reporter.py
```

### 5.2 主智能体完整实现

```python
# src/pstock_agent/stock_trader/agent.py

from pathlib import Path
from pstock_sdk import Agent, AgentBuilder, LLM

from .subagents.data_fetcher import create as create_data_fetcher
from .subagents.analyzer import create as create_analyzer
from .subagents.strategy_generator import create as create_strategy_generator
from .subagents.reporter import create as create_reporter


def create(llm: LLM) -> Agent:
    """创建 StockTrader 主智能体"""
    # 创建子智能体
    data_fetcher = create_data_fetcher(llm)
    analyzer = create_analyzer(llm)
    strategy_generator = create_strategy_generator(llm)
    reporter = create_reporter(llm)

    return (AgentBuilder()
        .with_name("stock_trader")
        .with_description("股票研究分析智能体 - 自动化多维度分析与策略生成")
        .with_instructions(_load_instructions())
        .with_max_steps(12)
        .with_children([
            data_fetcher,
            analyzer,
            strategy_generator,
            reporter,
        ])
        .with_memory_enabled(True)
        .build())


def _load_instructions() -> str:
    """加载系统提示词"""
    prompt_path = Path(__file__).parent / "prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    return """你是专业的股票研究分析智能体，负责协调子智能体完成全自动化的股票分析和策略生成流程。

## 工作流程

当收到用户的股票分析请求时，严格按照以下步骤执行：

1. **数据获取阶段**：调用 `data_fetcher` 子智能体获取股票的各类数据
2. **分析处理阶段**：调用 `analyzer` 子智能体进行多维度分析
3. **策略生成阶段**：调用 `strategy_generator` 子智能体生成交易策略
4. **报告生成阶段**：调用 `reporter` 子智能体生成最终报告
5. **结果返回**：将完整的分析报告返回给用户

## 子智能体说明

- data_fetcher: 获取股价、财务、情绪、宏观数据
- analyzer: 技术面、基本面、情绪面、宏观面分析
- strategy_generator: 基于分析结果和持仓生成交易策略
- reporter: 生成结构化的投资报告

## 重要原则

- 每个阶段只调用对应的子智能体，不要跳过或重复调用
- 如果某个子智能体执行失败，记录错误信息并尝试继续后续流程
- 最终报告必须包含所有四个维度的分析结论和交易策略
- 保持客观中立，明确标注不确定性
"""
```

### 5.3 实现优先级

#### Phase 1 - 核心框架（Week 1）
- 创建目录结构
- 实现四个子智能体的 `agent.py` 骨架（`create()` 函数）
- 实现主智能体 `agent.py`
- 完成基础的子智能体调用链路测试

#### Phase 2 - 数据层（Week 1-2）
- 实现 DataFetcher 的 4 个工具（yfinance/AKShare）
- 实现 data_quality Skill
- 数据格式标准化与错误处理

#### Phase 3 - 分析层（Week 2-3）
- 实现 Analyzer 的 4 个 Skills
- 实现 indicators 工具（集成 TA-Lib）
- 分析结论结构化输出

#### Phase 4 - 策略层（Week 3）
- 实现 StrategyGenerator 的 tools（券商API集成）
- 实现 4 个策略相关 Skills
- 风控检查逻辑实现

#### Phase 5 - 报告层（Week 3-4）
- 实现 Reporter 的 report_template Skill
- 实现 format 工具
- 报告模板优化

#### Phase 6 - 完善与测试（Week 4）
- 端到端流程测试
- 异常场景覆盖
- 文档完善

### 5.4 技术选型

| 组件 | 推荐方案 | 说明 |
|-----|---------|------|
| 股价数据 | yfinance / AKShare | 国际市场用 yfinance，A股用 AKShare |
| 财务数据 | AKShare | 支持 A 股财务报表 |
| 技术指标 | TA-Lib | 行业标准技术分析库 |
| 情绪数据 | 东方财富 / 同花顺API | 需调研可用 API |
| 宏观数据 | FRED | 美联储数据最权威 |
| 券商API | Interactive Brokers / 富途 | 根据目标市场选择 |

### 5.5 依赖项

```toml
# pyproject.toml

[project]
name = "pstock-agent"
version = "0.1.0"
dependencies = [
    "pstock-sdk = { path = ../pstock_sdk }",
]

[tool.uv.dependencies]
yfinance = ">=0.2.0"
akshare = ">=1.12.0"
ta-lib = ">=0.4.0"
pandas = ">=2.0.0"
```

---

## 6. 使用方式

### 6.1 Python API

```python
import asyncio
from pstock_sdk import OpenAILLM
from pstock_agent.stock_trader import create_stock_trader


async def main():
    # 初始化 LLM
    llm = OpenAILLM(
        api_key="sk-xxx",
        options={"model": "gpt-4o"}
    )

    # 创建智能体
    agent = create_stock_trader(llm)

    # 执行分析
    result = await agent.run("分析 AAPL 股票")

    # 输出报告
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 命令行入口

```python
# src/pstock_agent/stock_trader/__main__.py

import asyncio
import sys
from pstock_sdk import OpenAILLM
from . import create_stock_trader


async def cli_main():
    llm = OpenAILLM.from_env()  # 从环境变量读取配置

    agent = create_stock_trader(llm)

    task = " ".join(sys.argv[1:]) or "分析 AAPL"

    result = await agent.run(task)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(cli_main())
```

### 6.3 包入口模块

```python
# src/pstock_agent/stock_trader/__init__.py
from .agent import create as create_stock_trader

__all__ = ["create_stock_trader"]
```

```python
# src/pstock_agent/__init__.py
from .stock_trader import create_stock_trader

__all__ = ["create_stock_trader"]
```

### 6.4 命令行使用

```bash
# 直接运行
python -m pstock_agent.stock_trader "分析 AAPL"

# 交互模式 (可选扩展)
python -m pstock_agent.stock_trader --interactive
```

### 6.5 输出报告示例

```
=== AAPL 综合分析报告 ===
生成时间: 2025-01-15 10:30:00

一、核心结论
   投资评级: [买入]
   目标价位: $195.00
   风险等级: [中]
   综合评分: 8.2/10

二、技术分析
   趋势判断: 周期向上，短期回调后延续升势
   关键点位: 支撑 $172.50 | 阻力 $185.00
   指标信号: MACD金叉 | RSI 58.2(中性偏多)

三、基本面分析
   估值水平: PE 28.5x，略高于行业均值(25.2x)
   财务健康: 现金流充沛，资产负债率健康
   盈利能力: ROE 15.6%，毛利率持续提升

四、市场情绪
   整体情绪: 积极
   资金流向: 近5日净流入 $2.3B
   分析师评级: 32家买入，5家持有，0家卖出

五、宏观环境
   行业周期: 消费电子回暖周期
   政策影响: 美联储利率维持高位，科技股估值承压

六、交易策略
   操作建议: [加仓 BUY]
   建议数量: 50股
   目标价位: $175.00 (回调入场)
   止损价位: $168.00
   止盈价位: $195.00
   优先级: 中等

   策略依据:
   - 技术面上升趋势延续，MACD金叉确认
   - 基本面稳健，长期持有价值较高
   - 当前持仓100股(市值$17,850)，占比8.2%
   - 目标仓位12%，建议加仓50股

   风控提醒:
   ⚠️ 单股权重将达14.2%，略超10%建议上限
   ⚠️ 科技股权重已达45%，建议关注行业集中度风险

七、风险提示
   - 中国市场竞争加剧，销量增速放缓
   - 高利率环境压制科技股估值
   - 监管政策变化可能影响服务业务

---
本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
```

---

## 附录

### A. 术语表

| 术语 | 说明 |
|-----|------|
| ReAct | 一种推理-行动框架，AI通过思考、行动、观察循环完成任务 |
| Skill | Claude 技能，封装特定领域知识和能力 |
| Tool | 可调用的工具，封装具体的功能实现 |
| AgentAdapterTool | 将子智能体包装为工具的适配器 |
| OHLCV | Open/High/Low/Close/Volume，K线数据格式 |

### B. 参考资料

- [PStock SDK Documentation](../src/pstock_sdk/README.md)
- [Claude Skills Specification](https://docs.anthropic.com/claude/docs/skills-for-claude)
- [TA-Lib Documentation](https://ta-lib.org/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/trading/ib-api.html)

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| 1.0.0 | 2025-01-15 | 初始设计文档（包含策略生成） | PStock Team |
| 2.0.0 | 2026-02-12 | 重构为编程式构建，移除 agent.json | PStock Team |

---

*文档结束*