"""Retry decorator using tenacity."""

from functools import wraps
from typing import Callable, Any, Type
import asyncio

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
        after_log,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False


def should_retry(exception: Exception) -> bool:
    """
    Determine if an exception should be retried.

    Args:
        exception: The exception to check

    Returns:
        bool: True if should retry, False otherwise
    """
    # Don't retry parameter validation errors
    if isinstance(exception, (ValueError, KeyError, AttributeError, TypeError)):
        return False

    # Don't retry authentication/permission errors
    error_msg = str(exception).lower()
    if any(keyword in error_msg for keyword in [
        "permission", "denied", "unauthorized", "forbidden",
        "authentication", "auth", "token", "api key"
    ]):
        return False

    # Retry network and transient errors
    return any(keyword in error_msg for keyword in [
        "timeout", "connection", "network", "temporary",
        "rate limit", "503", "502", "504"
    ])


def async_retry_tool(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    retry_on: tuple[Type[Exception]] = (Exception,),
):
    """
    Decorator for async tool execution with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        wait_min: Minimum wait time in seconds (default: 1s)
        wait_max: Maximum wait time in seconds (default: 10s)
        retry_on: Tuple of exception types to retry on (default: all exceptions)

    Returns:
        Decorated async function
    """
    if not TENACITY_AVAILABLE:
        # Fallback: simple retry without tenacity
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if not should_retry(e) or attempt == max_attempts - 1:
                            raise
                        wait_time = min(wait_min * (2 ** attempt), wait_max)
                        await asyncio.sleep(wait_time)
                raise last_exception  # Should not reach here
            return wrapper
        return decorator

    # Use tenacity for full-featured retry
    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
        retry=retry_if_exception_type(*retry_on),
        before_sleep=before_sleep_log(lambda retry_state: print(f"Retrying {retry_state.fn.__name__} (attempt {retry_state.attempt_number}/{max_attempts})...")),
        after_log=after_log(lambda retry_state: print(f"Failed after {retry_state.attempt_number} attempts")),
        reraise=True,
    )
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper

    return decorator


def sync_retry_tool(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    retry_on: tuple[Type[Exception]] = (Exception,),
):
    """
    Decorator for sync tool execution with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        wait_min: Minimum wait time in seconds (default: 1s)
        wait_max: Maximum wait time in seconds (default: 10s)
        retry_on: Tuple of exception types to retry on (default: all exceptions)

    Returns:
        Decorated function
    """
    if not TENACITY_AVAILABLE:
        # Fallback
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if not should_retry(e) or attempt == max_attempts - 1:
                            raise
                        import time
                        wait_time = min(wait_min * (2 ** attempt), wait_max)
                        time.sleep(wait_time)
                raise last_exception
            return wrapper
        return decorator

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
        retry=retry_if_exception_type(*retry_on),
        reraise=True,
    )
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return decorator


# Convenience decorators
retry_async_tool = async_retry_tool(max_attempts=3)
retry_sync_tool = sync_retry_tool(max_attempts=3)
