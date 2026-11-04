import asyncio
import logging

import grpc

logger = logging.getLogger("retry")

RETRYABLE_CODES = {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED}


class RetryPolicy:
    def __init__(self, max_attempts: int = 3, base_delay: float = 0.1):
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    async def execute(self, func):
        last_exc = None
        for attempt in range(self.max_attempts):
            try:
                return await func()
            except grpc.aio.AioRpcError as e:
                if e.code() not in RETRYABLE_CODES:
                    raise
                last_exc = e
                if attempt < self.max_attempts - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"Retry {attempt + 1}/{self.max_attempts - 1} after {delay}s, code={e.code().name}")
                    await asyncio.sleep(delay)
        raise last_exc
