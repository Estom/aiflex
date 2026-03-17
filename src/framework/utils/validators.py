"""
AI Flex Framework - JSON 验证工具

提供 JSON 验证相关的工具函数。
"""

import json
from pathlib import Path
from typing import Any


def validate_json_file(file_path: Path) -> dict[str, Any]:
    """
    验证并加载 JSON 文件

    Args:
        file_path: JSON 文件路径

    Returns:
        解析后的 JSON 对象

    Raises:
        ValueError: 文件不存在、不是文件、或 JSON 格式无效
    """
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {e}")


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """
    验证 JSON 对象包含必需字段

    Args:
        data: JSON 对象
        required_fields: 必需字段列表

    Raises:
        ValueError: 缺少必需字段
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
