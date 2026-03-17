#!/usr/bin/env python
"""
作家智能体使用示例

展示如何使用作家智能体创作小说。
"""

import asyncio
import os
from dotenv import load_dotenv

from src.agents.novelist import create_novelist_agent

load_dotenv()


async def example_basic():
    """示例 1：基本使用"""
    print("=== 示例 1：基本使用 ===\n")

    agent = create_novelist_agent("都市")

    result = await agent.run_async(
        "写一个都市重生小说，主角是程序员，重生到2010年，"
        "带着前世记忆抓住比特币的机会，建立商业帝国。"
    )

    print(f"\n创作结果：\n{result}")


async def example_cultivation():
    """示例 2：修仙小说"""
    print("=== 示例 2：修仙小说 ===\n")

    agent = create_novelist_agent("修仙")

    result = await agent.run_async(
        "写一个修仙小说，山村少年意外获得上古传承，"
        "踏上修仙之路，最终成为仙界巨擘。"
    )

    print(f"\n创作结果：\n{result}")


async def example_system():
    """示例 3：系统流小说"""
    print("=== 示例 3：系统流小说 ===\n")

    agent = create_novelist_agent("系统流")

    result = await agent.run_async(
        "写一个系统流小说，主角觉醒投资系统，"
        "可以看到未来的投资回报率，实现财富自由。"
    )

    print(f"\n创作结果：\n{result}")


async def example_multi_chapter():
    """示例 4：多章节创作"""
    print("=== 示例 4：多章节创作 ===\n")

    agent = create_novelist_agent("重生")

    prompts = [
        "第一章：重生回高考前夕，带着前世记忆如何准备？",
        "第二章：高考成绩公布，比前世提高100分",
        "第三章：填报志愿，选择哪所大学？",
    ]

    chapters = []
    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- 正在创作第 {i} 章 ---")
        result = await agent.run_async(prompt)
        chapters.append(result)
        print(f"第 {i} 章创作完成，字数：{len(result)} 字")

    print(f"\n=== 总计创作 {len(chapters)} 章 ===")


async def main():
    """主函数"""
    print("🎨 作家智能体示例\n")

    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误：请设置 OPENAI_API_KEY 环境变量")
        return

    # 选择要运行的示例
    examples = {
        "1": ("基本使用 - 都市重生", example_basic),
        "2": ("修仙小说", example_cultivation),
        "3": ("系统流小说", example_system),
        "4": ("多章节创作", example_multi_chapter),
    }

    print("请选择要运行的示例：")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    choice = input("\n请输入编号（1-4）: ").strip()

    if choice in examples:
        name, func = examples[choice]
        print(f"\n运行示例：{name}\n")
        await func()
    else:
        print("❌ 无效的选择")


if __name__ == "__main__":
    asyncio.run(main())
