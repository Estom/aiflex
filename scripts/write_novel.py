#!/usr/bin/env python
"""
运行小说家智能体创作小说
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径到 Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from agents.novelist import create_novelist_agent
from dotenv import load_dotenv

load_dotenv()


async def main():
    """主函数"""
    print("🎨 作家智能体启动...\n")

    # 检查 API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误：请设置 OPENAI_API_KEY 环境变量")
        return

    # 获取题材参数
    genre = sys.argv[1] if len(sys.argv) > 1 else "都市"

    # 创建智能体
    agent = create_novelist_agent(genre)

    print(f"✅ {genre}小说作家智能体已创建")
    print(f"📝 工作区：{agent.workspace_root}")

    # 检查 API 配置
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    timeout = os.getenv("OPENAI_TIMEOUT", "300")

    print(f"\n🔧 API 配置：")
    print(f"   API Base: {api_base}")
    print(f"   Model: {model}")
    print(f"   Timeout: {timeout}秒")

    # 检查 API Key 是否有效
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-..."):
        print("\n⚠️  警告：OPENAI_API_KEY 未设置或使用示例值！")
        print("   请在 .env 文件中设置有效的 API Key")
        print("   如果在中国大陆，建议使用国内 API 镜像（如 DeepSeek、通义千问）")

    print("\n")

    # 创作提示词
    prompt = """
请创作一篇完整的{genre}小说，约3000字。

要求：
1. 完整的故事结构（开端、发展、高潮、结局）
2. 生动的角色描写
3. 悬念和爽点设置
4. 流畅的文笔
5. 结尾留有伏笔

故事方向：都市重生，主角是程序员林凡，重生到2010年，带着前世记忆改变命运，抓住互联网投资机会。

开始创作吧！
""".replace("{genre}", genre)

    print("🚀 开始创作...\n")

    try:
        # 运行智能体（Agent.run 返回 AgentRunResult）
        result = await agent.run(prompt)

        print("\n" + "="*60)
        print("✅ 创作完成！")
        print("="*60 + "\n")

        output = result.output if hasattr(result, 'output') else str(result)
        print(output)

        print("\n" + "="*60)
        print(f"📊 总字数：{len(output)} 字")
        print("="*60)

    except Exception as e:
        print(f"❌ 创作失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
