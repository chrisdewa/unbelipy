import asyncio
from datetime import datetime, timedelta
from typing import Dict

from aiolimiter import AsyncLimiter

class BucketRateLimit:
    """
    Stores information about rate limits
    """
    def __init__(self,
                 name: str,
                 prevent_rate_limits: bool
                 ):
        self.name = name
        self.prevent_rate_limits = prevent_rate_limits
        self.limit = None
        self.remaining = None
        self.reset = None
        self.retry_after = None
        self.first_run = False
        self.first_run_flag = asyncio.Event()
        self.lock = asyncio.Event()

    def __repr__(self):
        return (f"RateLimit(bucket={self.name}, limit={self.limit}, remaining={self.remaining}, "
                f"reset={self.reset}, retry_after={self.retry_after})")

    async def __aenter__(self):
        if self.prevent_rate_limits is True:
            if not self.first_run:
                self.first_run = True
                return
            else:
                while not self.first_run_flag.is_set():
                    await asyncio.sleep(0.1)

                if self.limit is not None:

                    if self.remaining <= self.limit*0.4:
                        self.lock.set()
                    while self.lock.is_set():
                        now = datetime.utcnow()
                        if now > (self.reset + timedelta(seconds=0.5)):
                            self.lock.clear()
                        else:
                            await asyncio.sleep(0.1)

    async def __aexit__(self, *args):
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
        self.global_limit = AsyncLimiter(15, 2)

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










