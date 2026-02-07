"""
示例：创建一个简单的市场分析 Agent

本示例展示如何使用 PStock SDK 创建一个能够分析市场新闻的 Agent
"""

import asyncio
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

from pstock_sdk import (
    Agent,
    AgentBuilder,
    AgentContext,
    OpenAILLM,
    OpenAIModelOptions,
    InMemoryExperienceStore,
    KnowledgeBaseRetrieveTool,
    setup_logger,
)
from pstock_sdk.integration import RagFlowClient, resolve_ragflow_config
from pstock_sdk.utils.logger import logger


async def create_market_analyst_agent() -> Agent:
    """
    创建市场分析 Agent

    Returns:
        Agent: 配置好的市场分析 Agent
    """
    # 加载环境变量
    load_dotenv()

    # 配置日志
    setup_logger("INFO")

    # 初始化 LLM
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")

    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE"),
            temperature=0.2,
        ),
    )

    # 创建经验存储
    experience_store = InMemoryExperienceStore()

    # 配置知识库（可选）
    knowledge_base = None
    try:
        ragflow_config = resolve_ragflow_config()
        ragflow = RagFlowClient(ragflow_config)
        knowledge_base = {
            "datasetIds": ["example-dataset-id"],
            "retrieval": {
                "similarityThreshold": 0.2,
                "vectorSimilarityWeight": 0.3,
                "recallCount": 5,
            },
        }
        logger.info("知识库已启用")
    except Exception as e:
        logger.warning(f"知识库未配置或配置错误: {e}")

    # 构建 Agent
    builder = (
        AgentBuilder()
        .with_name("market-analyst")
        .with_description("股市市场分析智能体")
        .with_instructions("""你是一位专业的股市分析师，擅长：
1. 分析财经新闻和市场事件
2. 评估新闻对股市的影响
3. 识别相关股票和投资机会
4. 提供客观、基于事实的分析

请用中文回答，保持专业和客观。""")
        .with_llm(llm)
        .with_max_steps(30)
        .with_workspace_root(os.getcwd())
        .with_experience_enabled(True)
        .with_experience_store(experience_store)
    )

    # 如果配置了知识库，添加知识库支持
    if knowledge_base:
        builder = builder.with_knowledge_base(knowledge_base)

    agent = builder.build()
    logger.info("市场分析 Agent 创建成功")

    return agent


async def main():
    """主函数"""
    print("=" * 60)
    print("PStock SDK - 市场分析 Agent 示例")
    print("=" * 60)
    print()

    # 创建 Agent
    agent = await create_market_analyst_agent()

    # 示例任务
    task = "请分析一下今天的 A 股市场概况，并给出你的投资建议。"

    print(f"任务: {task}")
    print("-" * 60)

    # 创建上下文
    context = AgentContext(
        session_id="market-analysis-demo",
        metadata={
            "user": "demo-user",
            "timestamp": "2025-01-01",
        },
    )

    # 运行 Agent
    result = await agent.run(task, context)

    # 输出结果
    print()
    print("=" * 60)
    print("Agent 分析结果:")
    print("=" * 60)
    print(result["output"])
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
