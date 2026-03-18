#!/usr/bin/env python
"""
API 连接测试脚本

测试 OpenAI API 配置是否正确。
"""

import os
import asyncio
from dotenv import load_dotenv

from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions

load_dotenv()


async def test_api_connection():
    """测试 API 连接"""
    print("🧪 API 连接测试\n")

    # 检查配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    timeout = float(os.getenv("OPENAI_TIMEOUT", "60"))

    print(f"📋 配置信息：")
    print(f"   API Key: {'已设置' if api_key else '未设置'}")
    print(f"   API Base: {api_base}")
    print(f"   Model: {model}")
    print(f"   Timeout: {timeout}秒")

    # 检查 API Key
    if not api_key or api_key.startswith("sk-...") or api_key == "your-api-key-here":
        print("\n❌ 错误：API Key 未设置或无效")
        print("   请在 .env 文件中设置有效的 OPENAI_API_KEY")
        print("   如果使用 DeepSeek，请访问 https://platform.deepseek.com/api_keys")
        print("   如果使用通义千问，请访问 https://dashscope.console.aliyun.com/apiKey")
        return False

    # 测试连接
    print("\n🔌 测试连接...")

    try:
        llm = OpenAILLM(
            api_key=api_key,
            options=OpenAIModelOptions(
                model=model,
                api_base=api_base,
                timeout=timeout,
            ),
        )

        # 发送测试请求
        response = await llm.chat([
            {"role": "user", "content": "测试连接，回复'成功'"}
        ])

        print("\n✅ API 连接成功！")
        print(f"   响应：{response['message']['content']}")
        return True

    except Exception as e:
        print(f"\n❌ API 连接失败：{e}")

        # 分析错误类型
        error_str = str(e).lower()

        if "timeout" in error_str:
            print("\n🔍 诊断：连接超时")
            print("   原因：API 服务器响应太慢或无法访问")
            print("   解决方案：")
            print("   1. 增加超时时间（修改 OPENAI_TIMEOUT）")
            print("   2. 使用国内 API 镜像（DeepSeek、通义千问）")
            print("   3. 检查网络连接")

        elif "401" in error_str or "unauthorized" in error_str:
            print("\n🔍 诊断：API Key 无效")
            print("   原因：API Key 不正确或已过期")
            print("   解决方案：")
            print("   1. 检查 API Key 是否正确")
            print("   2. 访问 API 提供商平台重新生成 Key")
            print("   3. 更新 .env 文件")

        elif "403" in error_str or "forbidden" in error_str:
            print("\n🔍 诊断：访问被拒绝")
            print("   原因：API 服务器拒绝访问")
            print("   解决方案：")
            print("   1. 检查 API Base URL 是否正确")
            print("   2. 确认 API Key 是否有访问权限")
            print("   3. 联系 API 提供商客服")

        elif "connection" in error_str or "network" in error_str:
            print("\n🔍 诊断：网络连接问题")
            print("   原因：无法连接到 API 服务器")
            print("   解决方案：")
            print("   1. 检查网络连接")
            print("   2. 尝试访问 API Base URL")
            print("   3. 检查防火墙设置")

        else:
            print(f"\n🔍 诊断：未知错误")
            print("   建议查看完整的错误信息")

        return False


async def test_chinese_models():
    """测试国内模型配置"""
    print("\n\n🌐 国内模型配置建议\n")

    print("推荐配置：\n")

    print("【DeepSeek（推荐）】")
    print("OPENAI_API_KEY=your-deepseek-api-key")
    print("OPENAI_API_BASE=https://api.deepseek.com/v1")
    print("OPENAI_MODEL=deepseek-chat")
    print("OPENAI_TIMEOUT=300")
    print("API Key: https://platform.deepseek.com/api_keys\n")

    print("【通义千问（推荐）】")
    print("OPENAI_API_KEY=your-qwen-api-key")
    print("OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1")
    print("OPENAI_MODEL=qwen-plus")
    print("OPENAI_TIMEOUT=300")
    print("API Key: https://dashscope.console.aliyun.com/apiKey\n")

    print("【智谱 AI】")
    print("OPENAI_API_KEY=your-zhipu-api-key")
    print("OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4")
    print("OPENAI_MODEL=glm-4")
    print("OPENAI_TIMEOUT=300")
    print("API Key: https://open.bigmodel.cn/usercenter/apikeys\n")


async def main():
    """主函数"""
    print("="*60)
    print("OpenClaw AI Flex - API 连接测试")
    print("="*60 + "\n")

    success = await test_api_connection()

    if not success:
        await test_chinese_models()
        print("\n" + "="*60)
        print("请修改 .env 文件后重新运行测试")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("✅ API 配置正确，可以正常使用")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
