# AI Flex 优化任务清单

## 任务概述

为 AI Flex 项目完成 P0 级别的高优先级优化工作。

## 项目信息

- 路径: /home/estom/work/aiflex
- 当前状态: 测试覆盖率约 30%
- 目标: 测试覆盖率 > 80%

---

## 任务 1: 完善测试体系（最高优先级）

### 目标
将测试覆盖率从 30% 提升到 80%+

### 具体任务

#### 1.1 创建测试目录结构
```
tests/
├── unit/
│   ├── test_agent_runtime.py      # ReAct 循环测试
│   ├── test_memory.py             # 记忆系统测试
│   ├── test_tools/                # 工具单元测试
│   │   ├── test_shell_tool.py
│   │   ├── test_file_tools.py
│   │   ├── test_web_tools.py
│   │   └── test_tool_registry.py
│   └── test_skills/
│       ├── test_skill_registry.py
│       └── test_skill_adapter.py
├── integration/
│   ├── test_multi_agent.py        # 多智能体协作测试
│   └── test_long_conversation.py  # 长对话压缩测试
├── performance/
│   └── benchmark_agent.py         # 性能基准测试
└── e2e/
    └── test_financial_analysis.py # 端到端场景测试
```

#### 1.2 核心模块测试要求

**test_agent_runtime.py**
- 测试 ReAct 循环的完整流程
- 测试最大步数限制
- 测试工具调用失败的处理
- 测试会话终止功能
- 测试流式输出模式

**test_memory.py**
- 测试记忆槽配置
- 测试记忆生成器
- 测试记忆记录创建
- 测试记忆更新逻辑

**test_tools/test_*.py**
- 测试每个内置工具的功能
- 测试错误处理
- 测试参数验证

**test_skills/test_skill_registry.py**
- 测试技能注册
- 测试技能查找
- 测试技能过滤

#### 1.3 集成测试要求

**test_multi_agent.py**
- 测试父 Agent 调用子 Agent
- 测试多级委托
- 测试循环引用检测

**test_long_conversation.py**
- 测试上下文压缩触发
- 测试压缩后的对话质量
- 测试记忆槽持久化

#### 1.4 性能测试要求

**benchmark_agent.py**
- 测量单个 Agent 执行时间
- 测量工具调用延迟
- 测量内存压缩性能
- 建立性能基准

#### 1.5 端到端测试要求

**test_financial_analysis.py**
- 使用真实 LLM 执行完整的金融分析任务
- 测试工具链的完整性
- 测试多轮对话

---

## 任务 2: 添加监控与可观测性

### 目标
实现基础的指标收集和追踪系统

### 具体任务

#### 2.1 创建 observability 模块

**src/sdk/agent/observability/metrics.py**
```python
# 使用 prometheus_client 库
# 指标：
# - agent_execution_duration_seconds
# - tool_calls_total{tool_name, status}
# - token_consumption_total{model}
# - memory_compression_count
# - memory_compression_duration_seconds
```

**src/sdk/agent/observability/tracing.py**
```python
# 使用 OpenTelemetry
# 追踪 Agent 执行流程
# 追踪工具调用
```

**src/sdk/agent/observability/events.py**
```python
# 事件总线系统
# 事件类型：
# - agent_started, agent_completed, agent_failed
# - tool_called, tool_succeeded, tool_failed
# - memory_compressed
```

#### 2.2 集成到 Agent Runtime
- 在关键节点记录指标
- 发布事件到事件总线
- 支持启用/禁用监控

#### 2.3 提供 /metrics 端点
- 集成到 FastAPI server（如果存在）
- 或提供独立的 metrics 服务

---

## 任务 3: 完善金融分析能力

### 目标
提供真实的金融分析工具和数据源

### 具体任务

#### 3.1 安装依赖
```bash
# 添加到 pyproject.toml dependencies
"yfinance>=0.2.44",
"pandas>=2.0.0",
"numpy>=1.24.0",
"ta>=0.11.0",  # 技术分析库
```

#### 3.2 创建金融工具

**src/agents/financial_analyst/tools/stock_fetcher.py**
```python
# 使用 yfinance 获取股票数据
# 工具函数：
# - get_stock_price(ticker)
# - get_stock_history(ticker, period)
# - get_company_info(ticker)
```

**src/agents/financial_analyst/tools/technical_indicators.py**
```python
# 计算技术指标
# 工具函数：
# - calculate_ma(ticker, period)
# - calculate_rsi(ticker, period)
# - calculate_macd(ticker)
# - calculate_bollinger_bands(ticker)
```

**src/agents/financial_analyst/tools/fundamental_analysis.py**
```python
# 基本面分析
# 工具函数：
# - get_pe_ratio(ticker)
# - get_market_cap(ticker)
# - get_revenue(ticker)
# - get_earnings(ticker)
```

#### 3.3 更新 agent.json
- 添加新工具到配置
- 更新提示词以使用新工具

#### 3.4 创建演示示例
- examples/financial_analysis_demo.py
- 展示如何使用真实数据进行分析

---

## 任务 4: 改进错误处理和重试机制

### 目标
提高系统稳定性和容错能力

### 具体任务

#### 4.1 添加依赖
```bash
# 添加到 pyproject.toml dependencies
"tenacity>=8.5.0",
```

#### 4.2 实现重试机制

**src/sdk/agent/tools/retry_decorator.py**
```python
# 使用 tenacity
# 指数退避：2s, 4s, 8s
# 最多重试 3 次
# 不重试参数错误、权限错误等
```

#### 4.3 改进错误提示

**在 agent_runtime.py 中**
```python
# 改进工具未找到的错误
# 显示可用工具列表
# 添加更多上下文信息
```

#### 4.4 添加日志
- 记录所有重试操作
- 记录失败的工具调用
- 记录错误堆栈

---

## 执行顺序

1. **任务 1**: 完善测试体系（最优先）
   - 先创建目录结构
   - 添加单元测试
   - 添加集成测试
   - 运行 pytest 验证
   - 生成覆盖率报告

2. **任务 2**: 添加监控与可观测性
   - 创建 observability 模块
   - 集成到 Runtime
   - 测试 metrics 输出

3. **任务 3**: 完善金融分析能力
   - 安装依赖
   - 创建金融工具
   - 测试数据获取
   - 创建演示

4. **任务 4**: 改进错误处理和重试机制
   - 实现重试装饰器
   - 改进错误提示
   - 添加日志

---

## 验证标准

### 测试验证
```bash
# 运行所有测试
uv run pytest -v

# 测试覆盖率
uv run pytest --cov=sdk --cov-report=term-missing
# 目标: > 80%

# 代码质量
uv run ruff check src/
uv run ruff format src/
uv run mypy src/
```

### 功能验证
- 所有新增测试通过
- 监控指标正确记录
- 金融工具能获取真实数据
- 重试机制工作正常

---

## 注意事项

1. **不要修改现有测试**，除非修复 bug
2. **遵循项目代码规范**（ruff, mypy）
3. **添加适当的文档注释**
4. **测试要覆盖关键路径**
5. **错误处理要完善**
6. **监控要轻量级，不影响性能**
7. **金融工具要有错误处理**

---

## 进度报告模板

完成任务后，按以下格式报告：

```
## 任务 X 完成报告

### 已完成的工作
- ...

### 测试结果
- pytest: [通过/失败]
- 覆盖率: [XX%]

### 遇到的问题
- ...

### 下一步计划
- ...
```
