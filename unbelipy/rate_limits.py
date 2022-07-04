"""
MIT License

Copyright (c) 2021 ChrisDewa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import (
    Dict, 
    List,
    Any
)

from aiohttp import ClientResponse
from aiolimiter import AsyncLimiter

__all__ = (
    "BucketHandler",
    "ClientRateLimits"
)

class BucketHandler:
    """
    Handles bucket-specific rate limits.
    """
    # these don't look like they should be class attributes...
    limit: int = None
    remaining: int = None
    reset: datetime = None
    retry_after: float = None
    cond = None
    prevent_429 = False

    def __init__(self, bucket: str) -> None:
        self.bucket: str = bucket

    def __repr__(self) -> str:
        return (
            f"RateLimit(bucket={self.bucket}, limit={self.limit}, remaining={self.remaining}, "
            f"reset={self.reset}, retry_after={self.retry_after})"
        )

    def check_limit_headers(self, response: ClientResponse) -> None:
        limits = {}
        header_attrs: Dict[str, str] = {
            'X-RateLimit-Limit': 'limit',
            'X-RateLimit-Remaining': 'remaining',
            'X-RateLimit-Reset': 'reset',
        }
        for key in header_attrs:
            value = response.headers.get(key)
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
            if self.remaining is not None and self.remaining == 0:
                now = datetime.utcnow()
                to_wait = (self.reset - now).total_seconds() + 1
                await asyncio.sleep(to_wait)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self.prevent_429 is True:
            self.cond.release()

class AsyncNonLimiter:
    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

class ClientRateLimits:
    buckets: Dict[str, BucketHandler] = dict()

    def __init__(self, prevent_rate_limits: bool) -> None:
        self.global_limiter = AsyncLimiter(20, 1) if prevent_rate_limits is True else AsyncNonLimiter()

    def currently_limited(self) -> List[str]:
        """
        This is useful to get the buckets which are currently being rate limited.

        Returns
        -------
        List[:class:`str`]
            A list of the rate limited buckets.
        """

        now = datetime.utcnow()
        limited = [k for k, v in self.buckets.items() if v.reset is not None and v.reset > now and v.remaining == 0]
        return limited

    def any_limited(self) -> bool:
        """
        This only returns ``True`` if one of the buckets are being rate limited.

        Returns
        -------
        bool
            ...
        """

        return any(self.currently_limited())

    def is_limited(self, bucket: str) -> bool:
        return bucket in self.currently_limited()
