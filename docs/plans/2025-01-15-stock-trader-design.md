# StockTrader 股票交易员智能体设计文档

**版本**: 1.0.0
**创建日期**: 2025-01-15
**作者**: PStock Team
**状态**: 设计阶段

---

## 目录

1. [概述与架构设计](#1-概述与架构设计)
2. [子智能体详细设计](#2-子智能体详细设计)
3. [数据流与接口设计](#3-数据流与接口设计)
4. [实现计划与目录结构](#4-实现计划与目录结构)
5. [配置示例与使用方式](#5-配置示例与使用方式)

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
| 子智能体划分 | 按处理阶段拆分 | 职责清晰，数据流向明确，便于并行优化 |
| 分析能力实现 | Skills + Tools | Skills提供领域知识，Tools提供计算能力 |
| 策略生成 | 独立子智能体 | 与分析解耦，便于接入不同券商API |
| 持仓数据 | 券商API集成 | 实时准确，支持实盘风控 |
| 报告格式 | 纯文本 | 易于集成，便于下游系统消费 |

---

## 2. 子智能体详细设计

### 2.1 DataFetcher（数据获取子智能体）

#### 职责
负责从各类数据源获取原始数据，为后续分析提供数据基础。

#### Tools 配置

| 工具名称 | 功能描述 | 输入 | 输出 |
|---------|---------|------|------|
| `stock_price` | 获取实时/历史股价数据 | symbol, period, range | OHLCV数据 |
| `financial_data` | 获取财务报表数据 | symbol, report_type, quarters | 财务指标 |
| `sentiment` | 获取市场情绪数据 | symbol, source | 情绪指标 |
| `macro_data` | 获取宏观经济指标 | indicator, date_range | 宏观数据 |

#### Skills 配置
- `data_quality`: 数据校验、缺失值处理、异常值检测

#### agent.json 配置
```json
{
  "name": "data_fetcher",
  "version": "1.0.0",
  "description": "专业金融数据获取智能体，支持股价、财务、舆情、宏观数据",
  "prompt": {
    "system": "你是数据获取专家，负责准确高效地获取各类金融数据。获取后进行基础校验，确保数据质量。"
  },
  "tools": {
    "auto_discover": true,
    "enabled": [],
    "disabled": []
  },
  "skills": {
    "sources": ["skills/"],
    "inline": []
  },
  "runtime": {
    "max_steps": 3,
    "experience_enabled": false
  }
}
```

### 2.2 Analyzer（分析处理子智能体）

#### 职责
基于获取的数据进行多维度分析，是核心分析引擎。

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

#### agent.json 配置
```json
{
  "name": "analyzer",
  "version": "1.0.0",
  "description": "多维度股票分析引擎，覆盖技术面、基本面、情绪面、宏观面",
  "prompt": {
    "system": "你是专业股票分析师，基于获取的数据进行全面深入的分析。每个维度都要给出明确的结论和依据。"
  },
  "skills": {
    "sources": ["skills/"],
    "inline": []
  },
  "tools": {
    "auto_discover": true,
    "enabled": ["indicators"],
    "disabled": []
  },
  "runtime": {
    "max_steps": 8,
    "experience_enabled": true
  }
}
```

### 2.3 StrategyGenerator（策略生成子智能体）

#### 职责
基于分析结果和当前持仓数据，生成具体交易策略，包含风控检查。

#### 核心功能
1. **持仓数据获取**：通过券商API获取当前账户持仓
2. **策略生成**：结合分析结论生成具体交易信号（买入/加仓/减仓/清仓）
3. **风控检查**：单股上限、总体仓位控制（软性提醒）
4. **组合影响评估**：计算交易对整体组合的影响

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

#### 输入数据格式

**来自 Analyzer**：
```json
{
  "symbol": "AAPL",
  "analyses": {
    "technical": { "trend": "bullish", "conclusion": "上升趋势延续" },
    "fundamental": { "conclusion": "基本面稳健" },
    "sentiment": { "conclusion": "市场情绪积极" },
    "macro": { "conclusion": "宏观环境利好" }
  }
}
```

**持仓数据（券商API）**：
```json
{
  "account_id": "xxx",
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "avg_cost": 165.00,
      "current_price": 178.50,
      "market_value": 17850.00,
      "pnl": 1350.00,
      "pnl_percent": 8.2
    }
  ],
  "cash": 50000.00,
  "total_value": 150000.00
}
```

#### 输出数据格式

**传递给 Reporter**：
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
    "reasoning": "技术面上升趋势延续，基本面稳健，当前仓位8.2%低于目标12%，建议逢低加仓",
    "priority": "MEDIUM"
  },
  "risk_alerts": [
    "单股权重将达14.2%，略超10%上限，请注意控制",
    "科技股权重已达45%，建议关注行业集中度"
  ],
  "portfolio_impact": {
    "current_weight": 8.2,
    "new_weight": 14.2,
    "cash_after": 32750.00,
    "sector_exposure": "+3.8%"
  }
}
```

#### agent.json 配置
```json
{
  "name": "strategy_generator",
  "version": "1.0.0",
  "description": "基于分析结果和持仓数据生成具体交易策略，包含风控检查",
  "prompt": {
    "system": "你是专业交易策略师，基于多维度分析和当前持仓情况，生成清晰具体的交易信号。风控检查采用软性提醒，超限时给出警告但允许策略生成。"
  },
  "tools": {
    "auto_discover": true,
    "enabled": ["get_positions", "risk_check", "calc_signals"],
    "disabled": []
  },
  "skills": {
    "sources": ["skills/"],
    "inline": []
  },
  "runtime": {
    "max_steps": 6,
    "experience_enabled": true
  }
}
```

### 2.4 Reporter（报告生成子智能体）

#### 职责
将分析结果和策略转化为用户友好的文本报告。

#### Skills 配置
- `report_template`: 定义报告结构、语气、格式规范

#### Tools 配置
- `format`: 报告格式化工具（章节生成、风险评级计算）

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

六、交易策略                  ← 新增章节
   操作建议: [加仓]
   建议数量: 50股
   目标价位: $175.00
   止损价位: $168.00
   止盈价位: $195.00
   策略依据: ...

   风控提醒:
   - 单股权重将达14.2%，略超10%上限
   - 科技股权重已达45%

七、风险提示
   - 主要风险点
```

#### agent.json 配置
```json
{
  "name": "reporter",
  "version": "1.0.0",
  "description": "分析报告生成智能体，结构化输出专业投资报告",
  "prompt": {
    "system": "你是专业报告撰写人，负责将分析结论和交易策略转化为清晰、专业、易读的投资报告。保持客观中立。"
  },
  "skills": {
    "sources": ["skills/"],
    "inline": []
  },
  "tools": {
    "auto_discover": true,
    "enabled": ["format"],
    "disabled": []
  },
  "runtime": {
    "max_steps": 3,
    "experience_enabled": false
  }
}
```

---

## 3. 数据流与接口设计

### 3.1 智能体间通信协议

子智能体之间通过 PStock 的 AgentAdapterTool 进行调用，数据传递采用标准化 JSON 格式。

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
      "ohlcv": [...],
      "volume": "45.2M"
    },
    "financial": {
      "pe": 28.5,
      "pb": 45.2,
      "roe": 0.156,
      "revenue": "383.3B",
      "net_income": "97.0B",
      "debt_ratio": 0.35
    },
    "sentiment": {
      "score": 0.72,
      "analyst_rating": "buy",
      "flow": "inflow",
      "news_sentiment": "positive"
    },
    "macro": {
      "rate": 5.25,
      "inflation": 3.2,
      "sector_outlook": "positive",
      "gdp_growth": 2.1
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
      "indicators": {
        "macd": "buy",
        "rsi": 58.2,
        "ma_signal": "golden_cross"
      },
      "conclusion": "上升趋势延续，建议回调买入"
    },
    "fundamental": {
      "valuation": {
        "status": "fair",
        "method": "DCF",
        "target_price": 195.00
      },
      "financial_health": "excellent",
      "competitive_advantage": "strong",
      "conclusion": "基本面稳健，长期持有价值较高"
    },
    "sentiment": {
      "overall": "positive",
      "key_factors": ["财报超预期", "机构增持"],
      "analyst_consensus": "buy",
      "conclusion": "市场情绪积极，资金持续流入"
    },
    "macro": {
      "impact": "positive",
      "risks": ["利率高位", "地缘政治"],
      "sector_cycle": "expansion",
      "conclusion": "宏观环境整体利好，需关注利率变化"
    }
  }
}
```

#### StrategyGenerator → Reporter 数据格式
```json
{
  "symbol": "AAPL",
  "analyses": {
    "technical": { "conclusion": "..." },
    "fundamental": { "conclusion": "..." },
    "sentiment": { "conclusion": "..." },
    "macro": { "conclusion": "..." }
  },
  "strategy": {
    "action": "BUY",
    "action_cn": "加仓",
    "quantity": 50,
    "target_price": 175.00,
    "stop_loss": 168.00,
    "take_profit": 195.00,
    "reasoning": "技术面上升趋势延续，基本面稳健，当前仓位8.2%低于目标12%，建议逢低加仓",
    "priority": "MEDIUM"
  },
  "risk_alerts": [
    "单股权重将达14.2%，略超10%上限，请注意控制",
    "科技股权重已达45%，建议关注行业集中度"
  ],
  "portfolio_impact": {
    "current_weight": 8.2,
    "new_weight": 14.2,
    "cash_after": 32750.00,
    "sector_exposure": "+3.8%"
  }
}
```

### 3.2 主智能体协调流程

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

### 3.3 错误处理策略

| 错误场景 | 处理方式 | 降级方案 |
|---------|---------|---------|
| 数据源超时 | 重试3次，指数退避 | 使用缓存数据或标记数据不可用 |
| 数据异常/缺失 | 触发 data_quality Skill 校验 | 跳过该维度，继续其他分析 |
| 分析失败 | 记录详细错误日志 | 返回简化结论，标注不确定性 |
| 券商API超时 | 重试2次，使用上次持仓 | 使用虚拟持仓数据继续 |
| 风控超限 | 记录警告，继续生成策略 | 在报告中醒目提示风险 |
| 子智能体不可用 | 自动降级到 Skills 模式 | 主智能体直接调用 Skills |

### 3.4 接口定义

#### get_positions Tool
```python
class GetPositionsTool(BaseTool):
    name: str = "get_positions"
    description: str = "从券商API获取当前账户持仓数据"

    async def execute(self, input: dict, context=None) -> str:
        # input: { broker: str, account_id: str }
        # 返回 JSON 格式的持仓数据
```

#### risk_check Tool
```python
class RiskCheckTool(BaseTool):
    name: str = "risk_check"
    description: str = "风控检查：单股上限、总体仓位、行业集中度"

    async def execute(self, input: dict, context=None) -> str:
        # input: { positions: [...], new_strategy: {...} }
        # 返回风险报告和警告列表
```

#### calc_signals Tool
```python
class CalcSignalsTool(BaseTool):
    name: str = "calc_signals"
    description: str = "基于分析结论和持仓计算交易信号"

    async def execute(self, input: dict, context=None) -> str:
        # input: { analyses: {...}, positions: [...] }
        # 返回交易信号（action/quantity/price等）
```

---

## 4. 实现计划与目录结构

### 4.1 完整目录结构

```
src/pstock_agent/stock_trader/
├── agent.json                      # 主智能体配置
├── prompt.md                       # 主智能体系统提示
├── README.md                       # 智能体使用说明
│
├── subagents/
│   │
│   ├── data_fetcher/               # 数据获取子智能体
│   │   ├── agent.json
│   │   ├── prompt.md
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── stock_price.py      # 股价数据（yfinance/AKShare）
│   │   │   ├── financial_data.py   # 财务数据（财报/估值指标）
│   │   │   ├── sentiment.py        # 市场情绪（舆情/资金流向）
│   │   │   └── macro_data.py       # 宏观数据（利率/通胀）
│   │   └── skills/
│   │       └── data_quality/
│   │           └── SKILL.md
│   │
│   ├── analyzer/                   # 分析处理子智能体
│   │   ├── agent.json
│   │   ├── prompt.md
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── indicators.py       # 技术指标计算（TA-Lib）
│   │   └── skills/
│   │       ├── technical/
│   │       │   └── SKILL.md        # 技术分析：MA/MACD/RSI/KDJ
│   │       ├── fundamental/
│   │       │   └── SKILL.md        # 基本面：PE/PB/ROE/DCF
│   │       ├── sentiment/
│   │       │   └── SKILL.md        # 情绪：资金流/舆情/评级
│   │       └── macro/
│   │           └── SKILL.md        # 宏观：利率/政策/行业
│   │
│   ├── strategy_generator/         # 策略生成子智能体
│   │   ├── agent.json
│   │   ├── prompt.md
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── get_positions.py    # 券商API持仓获取
│   │   │   ├── risk_check.py       # 风控检查工具
│   │   │   └── calc_signals.py     # 交易信号计算
│   │   └── skills/
│   │       ├── position_sizing/
│   │       │   └── SKILL.md        # 仓位管理策略
│   │       ├── entry_strategy/
│   │       │   └── SKILL.md        # 入场策略
│   │       ├── exit_strategy/
│   │       │   └── SKILL.md        # 出场策略
│   │       └── portfolio_mgmt/
│   │           └── SKILL.md        # 组合管理
│   │
│   └── reporter/                   # 报告生成子智能体
│       ├── agent.json
│       ├── prompt.md
│       ├── tools/
│       │   ├── __init__.py
│       │   └── format.py          # 报告格式化工具
│       └── skills/
│           └── report_template/
│               └── SKILL.md        # 报告模板与格式规范
│
├── tools/                          # 主智能体工具
│   ├── __init__.py
│   └── portfolio.py               # 组合管理工具（批量分析）
│
└── tests/                         # 单元测试
    ├── test_data_fetcher.py
    ├── test_analyzer.py
    ├── test_strategy_generator.py
    └── test_reporter.py
```

### 4.2 实现优先级

#### Phase 1 - 核心框架（Week 1）
- [ ] 创建目录结构和基础配置文件
- [ ] 实现主智能体 agent.json 和 prompt.md
- [ ] 搭建四个子智能体骨架
- [ ] 完成基础的子智能体调用链路测试

#### Phase 2 - 数据层（Week 1-2）
- [ ] 实现 DataFetcher 的4个工具（使用 yfinance/AKShare）
- [ ] 实现 data_quality Skill
- [ ] 数据格式标准化与错误处理

#### Phase 3 - 分析层（Week 2-3）
- [ ] 实现 Analyzer 的4个 Skills（逐步迭代）
- [ ] 实现 indicators 工具（集成 TA-Lib）
- [ ] 分析结论结构化输出

#### Phase 4 - 策略层（Week 3）
- [ ] 实现 StrategyGenerator 的 tools（券商API集成）
- [ ] 实现 4 个策略相关 Skills
- [ ] 风控检查逻辑实现

#### Phase 5 - 报告层（Week 3-4）
- [ ] 实现 Reporter 的 report_template Skill
- [ ] 实现 format 工具
- [ ] 报告模板优化（包含策略章节）

#### Phase 6 - 完善与测试（Week 4）
- [ ] 端到端流程测试
- [ ] 异常场景覆盖
- [ ] 文档完善

### 4.3 技术选型建议

| 组件 | 推荐方案 | 说明 |
|-----|---------|------|
| 股价数据 | yfinance / AKShare | yfinance国际市场，AKShare国内市场 |
| 财务数据 | AKShare / 财报API | 支持A股财务报表 |
| 技术指标 | TA-Lib | 行业标准技术分析库 |
| 情绪数据 | 东方财富 / 同花顺API | 需要调研可用的免费/付费API |
| 宏观数据 | FRED / TradingView | 美联储FRED数据最权威 |
| 券商API | Interactive Brokers / 富途 / 东方财富 | 根据目标市场选择 |

### 4.4 依赖项

```toml
[dependencies]
pstock-sdk = { path = "../pstock_sdk" }
pstock-framework = { path = "../pstock_framework" }

yfinance = "^0.2.0"      # 股价数据
akshare = "^1.12.0"     # A股数据
ta-lib = "^0.4.0"       # 技术指标
pandas = "^2.0.0"       # 数据处理

# 券商API（可选，根据选择）
ibapi = "^10.0.0"       # Interactive Brokers
# futu = "^6.0.0"       # 富途OpenD
```

---

## 5. 配置示例与使用方式

### 5.1 主智能体配置 (agent.json)

```json
{
  "name": "stock_trader",
  "version": "1.0.0",
  "description": "股票研究分析智能体 - 自动化多维度分析与策略生成",
  "model": null,
  "prompt": {
    "file": "prompt.md"
  },
  "skills": {
    "sources": [],
    "inline": []
  },
  "tools": {
    "auto_discover": true,
    "enabled": [],
    "disabled": []
  },
  "subagents": [
    { "name": "data_fetcher", "enabled": true },
    { "name": "analyzer", "enabled": true },
    { "name": "strategy_generator", "enabled": true },
    { "name": "reporter", "enabled": true }
  ],
  "runtime": {
    "max_steps": 12,
    "workspace_root": null,
    "mcp_lazy_load": false,
    "mcp_servers": [],
    "experience_enabled": true,
    "knowledge_base": null
  }
}
```

### 5.2 主智能体系统提示 (prompt.md)

```markdown
# StockTrader 主智能体

你是一个专业的股票研究分析智能体，负责协调子智能体完成全自动化的股票分析和策略生成流程。

## 工作流程

当收到用户的股票分析请求时，严格按照以下步骤执行：

1. **数据获取阶段**：调用 `data_fetcher` 子智能体获取股票的各类数据
2. **分析处理阶段**：调用 `analyzer` 子智能体进行多维度分析
3. **策略生成阶段**：调用 `strategy_generator` 子智能体生成交易策略
4. **报告生成阶段**：调用 `reporter` 子智能体生成最终报告
5. **结果返回**：将完整的分析报告返回给用户

## 重要原则

- 每个阶段只调用对应的子智能体，不要跳过或重复调用
- 如果某个子智能体执行失败，记录错误信息并尝试继续后续流程
- 最终报告必须包含所有四个维度的分析结论和交易策略
- 保持客观中立，明确标注不确定性
- 策略生成时结合当前持仓，给出具体可操作的建议

## 输出格式

最终输出必须为完整的文本报告，包含：核心结论、技术分析、基本面分析、市场情绪、宏观环境、交易策略、风险提示。
```

### 5.3 使用示例

#### Python API
```python
from pstock_framework import AgentFrameworkLoader
from pstock_sdk import OpenAILLM

# 初始化
llm = OpenAILLM(api_key="sk-xxx", options={"model": "gpt-4o"})
loader = AgentFrameworkLoader(agents_root="src/pstock_agent/", default_llm=llm)
await loader.load_all()

# 获取智能体
stock_trader = loader.get_agent("stock_trader")

# 执行分析
result = await stock_trader.run("分析 AAPL 股票")
print(result.output)
```

#### 命令行使用
```bash
# 交互模式
python -m pstock_agent.stock_trader --interactive

# 单次查询
python -m pstock_agent.stock_trader "分析 NVDA"

# 批量分析
python -m pstock_agent.stock_trader --batch AAPL,MSFT,GOOGL

# 指定券商账户
python -m pstock_agent.stock_trader "分析 TSLA" --broker ib --account U123456
```

### 5.4 输出报告示例

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
   量能分析: 近期放量上涨，资金介入明显

三、基本面分析
   估值水平: PE 28.5x，略高于行业均值(25.2x)
   财务健康: 现金流充沛，资产负债率健康
   盈利能力: ROE 15.6%，毛利率持续提升
   竞争优势: 生态壁垒稳固，创新能力强

四、市场情绪
   整体情绪: 积极
   资金流向: 近5日净流入 $2.3B
   分析师评级: 32家买入，5家持有，0家卖出
   关键驱动: iPhone销量超预期，AI功能获关注

五、宏观环境
   行业周期: 消费电子回暖周期
   政策影响: 美联储利率维持高位，科技股估值承压
   地缘风险: 供应链多元化策略降低地缘风险

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

   组合影响:
   - 当前权重: 8.2% → 建议后: 14.2%
   - 剩余现金: $50,000 → $32,750
   - 科技股权重: 41.2% → 45.0%

   风控提醒:
   ⚠️ 单股权重将达14.2%，略超10%建议上限
   ⚠️ 科技股权重已达45%，建议关注行业集中度风险

七、风险提示
   - 中国市场竞争加剧，销量增速放缓
   - 高利率环境压制科技股估值
   - 监管政策变化可能影响服务业务
   - 短期技术回调风险(RSI接近超买区)

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
| 仓位管理 | 控制每笔交易投入资金比例的策略 |
| 止损/止盈 | 限制亏损/锁定盈利的预设价格 |

### B. 参考资料

- [PStock Framework Documentation](../src/pstock_framework/README.md)
- [Claude Skills Specification](https://docs.anthropic.com/claude/docs/skills-for-claude)
- [TA-Lib Documentation](https://ta-lib.org/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Interactive Brokers API](https://www.interactivebrokers.com/en/trading/ib-api.html)

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| 1.0.0 | 2025-01-15 | 初始设计文档（包含策略生成） | PStock Team |

---

*文档结束*
