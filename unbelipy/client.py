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

import asyncio
from typing import (
    Any,
    Union, 
    Dict, 
    List, 
    Optional,
    Tuple
)
from inspect import stack
from json import dumps

from aiohttp import (
    ClientSession, 
    ClientResponse
)

from .errors import (
    TooManyRequests, 
    NotFound, 
    UnknownError,
    API_ERRORS
)
from .rate_limits import (
    BucketHandler, ClientRateLimits
)
from .constants import (
    API_BASE_URL
)
from .objects import (
    UserBalance,
    Guild
)

def _process_bal(
    bal_dict: dict, 
    guild_id: int, 
    bucket: str
) -> UserBalance:
    bal_dict.update({'guild_id': guild_id, 'bucket': bucket})
    bal_dict.pop('found', None)
    return UserBalance(**bal_dict)

def _process_leaderboard(
    users: dict, 
    guild_id: int, 
    bucket: str
) -> List[UserBalance]:
    return [_process_bal(user, guild_id, bucket) for user in users]

def _check_bal_args(
    cash: Any, 
    bank: Any, 
    reason: Any
) -> bool:
    """Checks types and content of arguments for edit and set balance methods"""

    if cash is None and bank is None:
        raise ValueError('An amount or "Infinity" must be specified for either cash or bank')

    for arg in (d := {'cash': cash, 'bank': bank}):
        value = d[arg]
        if value is None:
            continue
        else:
            if (t := type(value)) not in [int, str]:
                raise TypeError(f"{arg} can only be int or str but was {t}")
            elif t is str and value not in ['Infinity', '-Infinity']:
                raise ValueError(f'when {arg} is a str, "Infinity" is expected but "{value}" was received')

    if (t := type(reason)) is not str:
        raise TypeError(f'reason can only be str but was "{t}"')

    return True

class UnbeliClient:
    """
    The client to interact with UnbelievaBoat's API.

    Parameters:
        token (str): The Authorization token which will be used when requesting data.
        prevent_rate_limits (Optional[bool]): Whether the client will sleep through ratelimits to prevent 429 errors. This defaults to ``True``.
        retry_rate_limits (Optional[bool]): Whether the client will sleep and retry after 429 errors. This defaults to ``False``.

    Attributes:
        rate_limits:
            Dictionary containing information on the rate limit status of the client in the API.
                keys:
                    X-RateLimit-Limit: The number of requests that can be made.
                    X-RateLimit-Remaining: The number of remaining requests that can be made.
                    X-RateLimit-Reset: datetime to when the rate limit resets
                    retry_after: seconds to wait before being able to make another request

    Errors:
        All special error classes are found under unbelipy.errors:
            Exceptions for http status codes:
                400: BadRequest,
                401: Unauthorized,
                403: Forbidden,
                404: NotFound
                429: TooManyRequests,
                500: InternalServerError
    """

    _BASE_URL = API_BASE_URL
    _BASE_URL_LEN = len(_BASE_URL)
    _MEMBER_URL = _BASE_URL + '/guilds/{guild_id}/users/{member_id}'

    def __init__(
        self,
        token: str,
        *,
        prevent_rate_limits: Optional[bool] = True,
        retry_rate_limits: Optional[bool] = False
    ) -> None:
        self._headers: Dict[str, Any] = {
            "Accept": "application/json",
            'Authorization': token
        }
        self._prevent_rate_limits: bool = prevent_rate_limits
        self._retry_rate_limits: bool = retry_rate_limits

        self.rate_limits: ClientRateLimits = ClientRateLimits(prevent_rate_limits=prevent_rate_limits)

    async def get_permissions(
        self, 
        guild_id: int
    ) -> int:
        """
        Returns the application's permissions for the specified guild's ID.

        Parameters:
            guild_id (int): The target guild's ID.

        Raises:
            TypeError
                You did not pass an ``int`` to the ``guild_id`` parameter.

        Returns:
            int
                ...
        """
        if (t := type(guild_id)) is not int:
            raise TypeError(f"guild_id must be an int but {t} was received")

        method = 'GET'
        url = self._base_url + f"/applications/@me/guilds/{guild_id}"
        bucket = method + url[self._base_url_len:]

        return await self._request(method=method, url=url, bucket=bucket)

    async def get_guild(
        self, 
        guild_id: int
    ) -> Guild:
        """
        Retrieves a guild from the API.

        Parameters:
            guild_id (int): The target guild's ID.
    
        Raises:
            TypeError
                You did not pass an ``int`` to the ``guild_id`` parameter.

        Returns:
            Guild
                A dataclass containing information on the retrieved guild.
        """

        if (t := type(guild_id)) is not int:
            raise TypeError(f"guild_id must be an int but {t} was received")

        method = 'GET'
        url = f"{self._base_url}/guilds/{guild_id}"
        bucket = method + url[self._base_url_len:]

        return await self._request(method=method, url=url, bucket=bucket)

    async def get_leaderboard(
        self,
        guild_id: int,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 1,
        page: Optional[int] = None
    ) -> Union[
        List[UserBalance],
        Dict[str, Union[int, List[UserBalance]]]
    ]:
        """
        Retrieves the leaderboard for a guild.

        Parameters:
            guild_id (int): id of the guild
            sort (str): pass 'cash', 'bank' or 'total' to sort accordingly
            limit (int): amount of users to retrieve
            offset (int): retrieve users only from set place and below in the leaderboard
            page (int): page number to retrieve
                if specified returns a dictionary containing the list of user's leaderboard under key 'users' and
                additional 'page' with the current page and 'total_pages' with number available pages.

        Returns:
            Union[List[UserBalance], [Dict[str, Union[int, List[Userbalance]]]]]
                Dictionary containing leaderboard information.
        """

        bucket_path = f'/guilds/{guild_id}/users'
        url = self._base_url + bucket_path + '?'
        if sort is not None:
            if (t := type(sort)) is not str:
                raise TypeError(f'sort must be type str but was "{t}"')
            elif sort not in ['cash', 'bank', 'total']:
                raise ValueError(f'sort can only be "cash", "bank" or "total" but was "{sort}"')
            else:
                url += f"sort={sort}&"

        for arg in (d := {'limit': limit, 'offset': offset, 'page': page}):
            if d[arg] is not None:
                if (t := type(d[arg])) is not int:
                    raise TypeError(f'{arg} can only be type int but was {t}')
                else:
                    url += f"{arg}={d[arg]}&"

        method = 'GET'
        url = url[:-1]
        bucket = method + bucket_path
        return await self._request(method=method, url=url, bucket=bucket, guild_id=guild_id, page=page)

    async def get_balance(
        self, 
        guild_id: int, 
        user_id: int
    ) -> UserBalance:
        """
        Retrieves a user's balance.

        Parameters:
            guild_id (int): The guild's ID which the member belongs to.
            user_id (int): The user's ID. 

        Returns:
            UserBalance
                A dataclass containing information on the retrieved member's balance.
        """
        for arg in (d := {'guild_id': guild_id, 'user_id': user_id}):
            if (t := type(d[arg])) is not int:
                raise TypeError(f"{arg} can only be int but was {t}")
        method = 'GET'
        url, route = self._get_member_url(guild_id, user_id)
        bucket = method + route
        return await self._request(method=method, url=url, bucket=bucket, guild_id=guild_id)

    async def edit_balance(
        self,
        guild_id: int,
        user_id: int,
        cash: Optional[Union[int, str]] = None,
        bank: Optional[Union[int, str]] = None,
        reason: Optional[str] = None
    ) -> UserBalance:
        """
        Increase or decrease the Member's balance by a value given in the params.
        To decrease the balance, provide a negative number.

        Parameters:
            guild_id (int): The guild's ID which the member belongs to.
            user_id (int): The user's ID.
            cash (Optional[Union[int, str]]): Amount to modify the member's cash amount to.
            bank (Optional[Union[int, str]]): Amount to modify the member's bank amount to.
            reason (Optional[str]): The reason to why the balance was modified.

        Returns:
            UserBalance
                A dataclass containing information on the member's newly modified balance.
        """

        if _check_bal_args(cash, bank, reason):
            data: Dict[str, Any] = {
                'cash': cash, 
                'bank': bank, 
                'reason': reason
            }

            method = 'PATCH'
            url, route = self._get_member_url(guild_id, user_id)
            bucket = method + route
            return await self._request(method=method, url=url, bucket=bucket, data=dumps(data), guild_id=guild_id)

    async def set_balance(
        self,
        guild_id: int,
        user_id: int,
        cash: Optional[Union[int, str]] = None,
        bank: Optional[Union[int, str]] = None,
        reason: Optional[str] = None
    ) -> UserBalance:
        """
        Patches a user's balance to a given amount.
        At least one of cash, or bank must be specified.
        Parameters:
            guild_id (int): The guild's ID which the member belongs to.
            user_id (int): The user's ID.
            cash (Optional[Union[int, str]]): Amount to set the member's cash amount to. If this is a string, it must be set to "Infinite".
            bank (Optional[Union[int, str]]): Amount to set the member's bank amount to. If this is a string, it must be set to "Infinite".
            reason (Optional[str]): The reason to why the balance was patched.

        Returns:
            UserBalance
                A dataclass containing information on the member's newly set balance.
        """

        if _check_bal_args(cash, bank, reason):
            data: Dict[str, Any] = {
                'cash': cash, 
                'bank': bank, 
                'reason': reason
            }
            method = 'PUT'
            url, route = self._get_member_url(guild_id, user_id)
            bucket = method + route
            return await self._request(method=method, url=url, bucket=bucket, data=dumps(data), guild_id=guild_id)

    def _get_member_url(self, guild_id: int, member_id: int) -> Tuple(str, str):
        url = self._member_url.format(guild_id=guild_id, member_id=member_id)
        route = url[self._base_url_len:-len(str(member_id))] + ':id'
        return url, route

    @staticmethod
    def _get_caller() -> stack:
        return stack()[2][3]

    def _get_bucket_handler(self, bucket: str) -> BucketHandler:
        bucket_handler = self.rate_limits.buckets.get(bucket)
        if bucket_handler is None:
            bucket_handler = self.rate_limits.buckets[bucket] = BucketHandler(bucket=bucket)
        return bucket_handler

    async def _request(
        self,
        method: str,
        url: str,
        bucket: str,
        data: Optional[str] = None,
        caller = None,
        **kwargs
    ) -> Any:
        """
        Processes requests to the Unbelievaboat's API.

        Parameters:
            method (str): The method used for the request, can be 'PUT', 'PATCH' or 'GET'.
            url (str): URL to request to/from.
            data (json str): server data
            kwargs:
                guild_id: id (int) of the guild
                page: int number of page in the case of get_leaderboard
        """

        cs = ClientSession(headers=self._headers)
        if caller is None:
            caller = self._get_caller()
        guild_id = kwargs.pop('guild_id', None)
        page = kwargs.pop('page', None)

        if method == 'PUT':
            request_manager = cs.put(url=url, data=data)
        elif method == 'PATCH':
            request_manager = cs.patch(url=url, data=data)
        else:  # defaults to 'GET'
            request_manager = cs.get(url=url)

        bucket_handler: BucketHandler = self._get_bucket_handler(bucket)
        bucket_handler.prevent_429 = self._prevent_rate_limits
        async with self.rate_limits.global_limiter:
            async with bucket_handler as bh:
                async with cs:
                    r = await request_manager
                    bh.check_limit_headers(r)  # sets up the bucket rate limit attributes w/ response headers
                    response_data = await r.json()
                try:
                    if await self._check_response(response=r, bucket=bucket):
                        if caller in ['edit_balance', 'set_balance', 'get_balance']:
                            return _process_bal(response_data, guild_id, bucket)
                        elif caller == 'get_leaderboard':
                            if page is None:
                                return _process_leaderboard(response_data, guild_id, bucket)
                            else:
                                response_data['users'] = _process_leaderboard(response_data['users'], guild_id, bucket)
                                return response_data
                        elif caller == 'get_permissions':
                            return response_data['permissions']
                        elif caller == 'get_guild':
                            response_data['bucket'] = bucket
                            return Guild(**response_data)
                except TooManyRequests as E:
                    if self._retry_rate_limits is True:
                        timeout = response_data['retry_after'] / 1000 + 1
                        await asyncio.sleep(timeout)
                        # reschedule same request
                        return await self._request(method, url, bucket, data, caller=caller, **kwargs)
                    else:
                        raise E

    async def _check_response(self, response: ClientResponse, bucket: str):
        """Checks API response for errors. Returns True only on status 200"""
        status = response.status
        reason = response.reason
        data = await response.json()

        if status == 200:
            return True
        elif status == 429:
            message = data['message']
            if 'global' in data:
                text = f"Global rate limit. {data['message']}"
            elif retry_after := data.get('retry_after'):
                retry_after = int(retry_after) / 1000
                bucket_handler = self._get_bucket_handler(bucket)
                bucket_handler.retry_after = retry_after
                text = f"{message} retry after: {retry_after}s"
            else:
                text = f"{message}"
            raise TooManyRequests(text + f', bucket: {bucket}')
        elif status == 404:
            raise NotFound(f'Error Code: "{status}" Reason: "{reason}", bucket {bucket}')
        else:
            error_text = f'Error code: "{status}" Reason: "{reason}"'
            if status in API_ERRORS:
                raise API_ERRORS[status](error_text)
            else:
                raise UnknownError(error_text)
