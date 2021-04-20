import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Dict

from aiolimiter import AsyncLimiter


class BucketRateLimit:
    """
    Stores information about rate limits
    """
    limit = None
    remaining = None
    reset = None
    retry_after = None
    sem = None

    def __init__(self,
                 name: str,
                 prevent_rate_limits: bool
                 ):
        self.name = name
        self.prevent_rate_limits = prevent_rate_limits

    def __repr__(self):
        return (f"RateLimit(bucket={self.name}, limit={self.limit}, remaining={self.remaining}, "
                f"reset={self.reset}, retry_after={self.retry_after})")

    async def __aenter__(self):
        if self.prevent_rate_limits is True:
            sem_size_dict = defaultdict(lambda: 9, get_balance=5, get_permissions=20)
            self.sem = self.sem or asyncio.Semaphore(sem_size_dict[self.name], loop=asyncio.get_running_loop())
            await self.sem.acquire()

            route_offset = defaultdict(lambda: 1.1, get_guild=2, get_permissions=0)
            route_offset['get_guild'] = 2
            now = datetime.utcnow()
            to_wait = ((self.reset or now) - now).total_seconds() + route_offset[self.name]

            await asyncio.sleep(to_wait)

    async def __aexit__(self, *args):
        if self.prevent_rate_limits:
            self.sem.release()


class AsyncNonLimiter:
    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ClientRateLimits:
    """
    Defines the http paths to the API to associate their rate limit information
    """

    def __init__(self, prevent_rate_limits: bool):
        self.prevent_rate_limits = prevent_rate_limits
        self.get_balance = BucketRateLimit(name='get_balance', prevent_rate_limits=prevent_rate_limits)
        self.edit_balance = BucketRateLimit(name='edit_balance', prevent_rate_limits=prevent_rate_limits)
        self.set_balance = BucketRateLimit(name='set_balance', prevent_rate_limits=prevent_rate_limits)
        self.get_leaderboard = BucketRateLimit(name='get_leaderboard', prevent_rate_limits=prevent_rate_limits)
        self.get_guild = BucketRateLimit(name='get_guild', prevent_rate_limits=prevent_rate_limits)
        self.get_permissions = BucketRateLimit(name='get_permissions', prevent_rate_limits=prevent_rate_limits)
        self.global_limit = AsyncLimiter(15, 2) if prevent_rate_limits is True else AsyncNonLimiter()


    def __repr__(self):
        limited = self.any_currently_limited()
        return f"ClientRateLimits(currently_limited={limited})"

    def currently_limited(self) -> Dict[str, bool]:
        """
        Returns:
            dict containing bucket names (api routes) and bool if they're being rate limited
        """
        now = datetime.utcnow()
        all_limits = dict()
        for key in self.__dict__.keys():
            attr = getattr(self, key)
            all_limits[key] = (attr.reset > now and attr.remaining == 0) if attr.reset else False
        return all_limits

    def any_currently_limited(self) -> bool:
        """
        Returns:
            True if any bucket is being rate limited
        """
        return any(self.currently_limited().values())

    def is_bucket_limited(self, bucket: str):
        return self.currently_limited().get(bucket) is True
