---
name: weather-display
description: Displays formatted weather information including current conditions, temperature, forecast, humidity, wind, and other details for specified locations. Use when the user asks about weather, forecast, temperature, conditions, rain, sunny, or climate in a city/region. Trigger keywords: weather, forecast, temperature, 天气, 预报, 气温.
license: MIT
metadata:
  author: Grok Assistant
  version: "1.0.0"
---

# 天气信息展示技能

## 使用流程
1. **解析用户查询**：提取地点（城市、国家、地区），以及具体需求（当前天气、预报、小时预报等）。如果未指定地点，询问澄清或使用默认地点。
2. **获取数据**：在支持的环境中，使用工具或 `scripts/fetch_weather.py` 调用天气 API（如 OpenWeatherMap）。如果无法获取实时数据，基于知识或提示用户提供数据。
3. **格式化展示**：
   - 使用 Markdown 表格、表情符号提升可读性。
   - 先显示当前天气，再显示预报。
   - 处理边缘情况（如地点无效、API 错误）。
4. **输出原则**：简洁、美观、专业；支持中文/英文；保持响应友好。

## 展示模板
**🌤️ [地点] 天气**

**当前状况：**
- 温度： [temp]°C（体感 [feels_like]°C）
- 天气： [description] [emoji]
- 湿度： [humidity]%
- 风速： [wind_speed] km/h [direction]
- 气压： [pressure] hPa

**预报（如果请求）：**
| 日期/时间 | 最高/最低温 | 状况          | 降雨概率 |
|-----------|-------------|---------------|----------|
| 明天     | 18/12°C    | 多云 ☁️      | 20%     |
| 后天     | 20/15°C    | 小雨 🌧️      | 60%     |

## 示例
**用户**：东京的天气怎么样？  
**响应**：  
**🌸 东京，日本**  
**当前状况：**  
- 温度：15°C（体感14°C）  
- 天气：晴朗 ☀️  
- 湿度：60%  
- 风速：10 km/h 西风  

**未来 3 天预报：**  
（表格如上）

**用户**：北京明天会下雨吗？  
**响应**：直接聚焦预报部分，并说明概率。

## 边缘情况处理
- 地点模糊 → 询问具体城市（如“上海还是北京？”）。
- 无数据 → “暂无法获取实时数据，请检查 API 或提供更多信息。”
- 多天预报 → 默认显示 3-5 天，超出时询问用户需求。

此技能可与其他技能（如数据分析）组合使用。保持 SKILL.md 简洁（<5000 tokens），详细脚本/模板移到子文件夹。