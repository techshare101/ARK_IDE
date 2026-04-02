import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    *args,
    **kwargs,
) -> Any:
    """Retry an async function with exponential backoff."""
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                raise

            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

    raise last_exception


def retry(
    max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0
):
    """Decorator for retry with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                func, max_retries, base_delay, max_delay, 2.0, *args, **kwargs
            )

        return wrapper

    return decorator
