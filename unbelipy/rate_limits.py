import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from aiohttp import ClientResponse
from aiolimiter import AsyncLimiter


class BucketHandler:
    """
    Handles bucket specific rate limits
    flow:
        dict {
            bucket_name: BucketHandler
        }
    """
    limit: int = None
    remaining: int = None
    reset: datetime = None
    retry_after: float = None
    cond = None
    prevent_429 = False

    def __init__(self, bucket: str):
        self.bucket = bucket

    def __repr__(self):
        return (f"RateLimit(bucket={self.bucket}, limit={self.limit}, remaining={self.remaining}, "
                f"reset={self.reset}, retry_after={self.retry_after})")

    def check_limit_headers(self, r: ClientResponse):
        limits = dict()
        header_attrs = {
            'X-RateLimit-Limit': 'limit',
            'X-RateLimit-Remaining': 'remaining',
            'X-RateLimit-Reset': 'reset',
        }
        for key in header_attrs:
            value = r.headers.get(key)
            if value is not None:
                value = int(value)
                if key == 'X-RateLimit-Reset':
                    value = datetime.utcfromtimestamp(value / 1000)
            limits[header_attrs[key]] = value
        for k, v in limits.items():
            setattr(self, k, v)

    async def __aenter__(self):
        self.cond = self.cond or asyncio.Condition(loop=asyncio.get_running_loop())
        if self.prevent_429 is True:
            await self.cond.acquire()
        return self

    async def __aexit__(self, *args):
        if self.prevent_429 is True:
            if self.remaining is not None and self.remaining == 0:
                now = datetime.utcnow()
                to_wait = (self.reset - now).total_seconds() + 1
                await asyncio.sleep(to_wait)
            self.cond.release()


class AsyncNonLimiter:
    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ClientRateLimits:
    buckets: Dict[str, BucketHandler] = dict()

    def __init__(self, prevent_rate_limits: bool):
        self.global_limiter = AsyncLimiter(20, 1) if prevent_rate_limits is True else AsyncNonLimiter()

    def currently_limited(self) -> List[str]:
        """
        Returns:
            Returns a list of the buckets (str) that are currently being limited.
        """
        now = datetime.utcnow()
        limited = [k for k, v in self.buckets.items() if v.reset is not None and v.reset > now and v.remaining == 0]
        return limited

    def any_limited(self) -> bool:
        """
        Returns:
            True if any bucket is being rate limited
        """
        return any(self.currently_limited())

    def is_limited(self, bucket: str):
        return bucket in self.currently_limited()

