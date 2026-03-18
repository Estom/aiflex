# 小说家智能体故障排除指南

## 🔍 问题诊断

### 问题：API 调用超时

**错误信息**：
```
openai.APITimeoutError: Request timed out.
```

---

## ✅ 常见原因和解决方案

### 1️⃣ API 访问被封锁（中国大陆）

**原因**：
使用 OpenAI 官方 API `https://api.openai.com/v1`，在中国大陆被封锁。

**解决方案**：使用国内 API 镜像

#### 选项 A：DeepSeek（推荐）

```bash
# 编辑 .env 文件
OPENAI_API_KEY=your-deepseek-api-key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TIMEOUT=300
```

**获取 API Key**：
1. 访问 https://platform.deepseek.com/
2. 注册/登录
3. 进入 API Keys 页面
4. 创建新的 API Key

#### 选项 B：通义千问（推荐）

```bash
OPENAI_API_KEY=your-qwen-api-key
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
OPENAI_TIMEOUT=300
```

**获取 API Key**：
1. 访问 https://dashscope.console.aliyun.com/
2. 登录阿里云账号
3. 进入 API-KEY 管理
4. 创建新的 API Key

#### 选项 C：智谱 AI

```bash
OPENAI_API_KEY=your-zhipu-api-key
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4
OPENAI_MODEL=glm-4
OPENAI_TIMEOUT=300
```

**获取 API Key**：
1. 访问 https://open.bigmodel.cn/
2. 注册/登录
3. 进入 API Keys 页面
4. 创建新的 API Key

---

### 2️⃣ API Key 无效或未设置

**原因**：
`.env` 文件中的 `OPENAI_API_KEY` 未设置或使用示例值。

**解决方案**：

#### 检查配置

```bash
cd /home/estom/work/aiflex
cat .env | grep OPENAI_API_KEY
```

#### 修复配置

```bash
# 编辑 .env 文件
vim .env

# 修改 API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
```

#### 测试连接

```bash
python scripts/test_api.py
```

---

### 3️⃣ 超时时间太短

**原因**：
默认超时时间太短，长请求容易超时。

**解决方案**：

#### 增加超时时间

```bash
# 编辑 .env 文件
OPENAI_TIMEOUT=600  # 10 分钟
```

#### 在代码中设置

```python
llm = OpenAILLM(
    api_key=api_key,
    options=OpenAIModelOptions(
        model=model,
        api_base=api_base,
        timeout=600,  # 10 分钟
    ),
)
```

---

### 4️⃣ 网络连接问题

**原因**：
网络不稳定或无法访问 API 服务器。

**解决方案**：

#### 测试网络连接

```bash
# 测试 API Base 是否可访问
curl -I https://api.deepseek.com/v1
```

#### 使用代理

```bash
# 设置代理
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 然后运行智能体
python scripts/write_novel.py 都市
```

---

## 🔧 快速修复步骤

### 步骤 1：运行 API 测试

```bash
cd /home/estom/work/aiflex
python scripts/test_api.py
```

### 步骤 2：根据错误选择解决方案

| 错误 | 解决方案 |
|------|---------|
| **Timeout** | 增加超时时间，使用国内 API |
| **Unauthorized (401)** | 更新 API Key |
| **Forbidden (403)** | 检查 API 权限 |
| **Connection Error** | 检查网络，使用代理 |

### 步骤 3：修改 .env 配置

使用 DeepSeek（推荐）：
```bash
cp .env.example .env
vim .env

# 修改为 DeepSeek 配置
OPENAI_API_KEY=your-deepseek-api-key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TIMEOUT=300
```

### 步骤 4：重新测试

```bash
python scripts/test_api.py
```

### 步骤 5：运行智能体

```bash
.venv/bin/python scripts/write_novel.py 都市
```

---

## 📊 国内 API 镜像对比

| API | 地址 | 模型 | 优势 | 获取 Key |
|-----|------|------|------|---------|
| **DeepSeek** | https://api.deepseek.com/v1 | deepseek-chat | 国内访问快，价格低 | https://platform.deepseek.com/api_keys |
| **通义千问** | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus | 阿里云服务稳定 | https://dashscope.console.aliyun.com/apiKey |
| **智谱 AI** | https://open.bigmodel.cn/api/paas/v4 | glm-4 | 智能中文理解好 | https://open.bigmodel.cn/usercenter/apikeys |

---

## 🎯 推荐配置

### 配置 1：DeepSeek（推荐，性价比最高）

```bash
OPENAI_API_KEY=your-deepseek-api-key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_TIMEOUT=300
```

### 配置 2：通义千问（推荐，稳定性好）

```bash
OPENAI_API_KEY=your-qwen-api-key
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
OPENAI_TIMEOUT=300
```

### 配置 3：智谱 AI（推荐，中文理解好）

```bash
OPENAI_API_KEY=your-zhipu-api-key
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4
OPENAI_MODEL=glm-4
OPENAI_TIMEOUT=300
```

---

## 🐛 调试技巧

### 1. 查看 OpenAI 日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 然后运行智能体
```

### 2. 使用 curl 测试

```bash
# 测试 API 连接
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "测试"}],
    "max_tokens": 10
  }'
```

### 3. 查看 Python 环境

```bash
# 检查 Python 版本
python --version

# 检查已安装的包
.venv/bin/pip list | grep openai
```

---

## 📞 获取帮助

### DeepSeek 客服
- 文档：https://platform.deepseek.com/docs/
- 社区：https://github.com/deepseek-ai/

### 通义千问客服
- 文档：https://help.aliyun.com/zh/dashscope/
- 控制台：https://dashscope.console.aliyun.com/

### 智谱 AI 客服
- 文档：https://open.bigmodel.cn/dev/api
- 控制台：https://open.bigmodel.cn/usercenter/apikeys

---

**如果以上方法都无法解决问题，请提供完整的错误信息以便进一步诊断。** 🐛
