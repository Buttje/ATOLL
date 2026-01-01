"""Async utility functions."""

import asyncio
from collections.abc import Coroutine
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


async def timeout_wrapper(
    coro: Coroutine[Any, Any, T],
    timeout_seconds: float = 30.0,
) -> Optional[T]:
    """Wrap a coroutine with a timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return None


async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    **kwargs,
) -> Optional[T]:
    """Retry an async function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(delay * (2**attempt))
    return None
