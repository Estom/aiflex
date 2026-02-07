"""
Logger - 日志工具

基于 loguru 的日志配置
"""

import sys
from loguru import logger
from pathlib import Path


def setup_logger(log_level: str = "INFO") -> None:
    """
    配置日志系统

    Args:
        log_level: 日志级别
    """
    # 移除默认 handler
    logger.remove()

    # 添加控制台 handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
    )

    # 添加文件 handler
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger.add(
        logs_dir / "error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="10 MB",
        retention="30 days",
    )

    logger.add(
        logs_dir / "combined.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="10 MB",
        retention="30 days",
    )


# 导出 logger
__all__ = ["logger", "setup_logger"]
