from datetime import datetime
from typing import Optional, Dict

class RateLimitInfo:
    """
    Stores information about rate limits
    """

    def __init__(self,
                 bucket: str,
                 limit: Optional[int] = None,
                 remaining: Optional[int] = None,
                 reset: Optional[datetime] = None,
                 retry_after: Optional[float] = None):
        self.bucket = bucket
        self.limit = limit
        self.remaining = remaining
        self.reset = reset
        self.retry_after = retry_after

    def __repr__(self):
        return (f"RateLimit(bucket={self.bucket}, limit={self.limit}, remaining={self.remaining}, "
                f"reset={self.reset}, retry_after={self.retry_after})")


class ClientRateLimits:
    """
    Defines the http paths to the API to associate their rate limit information
    """

    def __init__(self,
                 get_balance: RateLimitInfo = RateLimitInfo(bucket='get_balance'),
                 edit_balance: RateLimitInfo = RateLimitInfo(bucket='edit_balance'),
                 set_balance: RateLimitInfo = RateLimitInfo(bucket='set_balance'),
                 get_leaderboard: RateLimitInfo = RateLimitInfo(bucket='get_leaderboard'),
                 get_guild: RateLimitInfo = RateLimitInfo(bucket='get_guild'),
                 get_permissions: RateLimitInfo = RateLimitInfo(bucket='get_permissions'),
                 global_rates: RateLimitInfo = RateLimitInfo(bucket='global_rates')
                 ):
        self.get_balance = get_balance
        self.edit_balance = edit_balance
        self.set_balance = set_balance
        self.get_leaderboard = get_leaderboard
        self.get_guild = get_guild
        self.get_permissions = get_permissions
        self.global_rates = global_rates

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