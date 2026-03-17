"""
Memory Module - 记忆模块

该模块提供记忆存储、记忆生成、上下文压缩等功能。
"""

from .compressor import (
    CONTEXT_COMPRESSION_PROMPT,
    ContextCompressor,
)
from .memory import (
    MEMORY_GENERATION_PROMPT,
    MemoryGenerator,
    MemoryRecord,
    MemorySlotConfig,
)

__all__ = [
    # Memory Storage
    "MemoryRecord",
    "MemorySlotConfig",
    # Memory Generation
    "MemoryGenerator",
    "MEMORY_GENERATION_PROMPT",
    # Context Compression
    "ContextCompressor",
    "CONTEXT_COMPRESSION_PROMPT",
]
