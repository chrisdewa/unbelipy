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

import logging
import asyncio
import atexit
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

from aiohttp import ClientSession, ClientResponse

from .errors import BadRequest, Unauthorized, Forbidden, NotFound, TooManyRequests, InternalServerError, UnknownException
from .rate_limits import BucketHandler, ClientRateLimits
from .constants import API_BASE_URL
from .objects import UserBalance, Guild

__all__ = (
    "UnbeliClient"
)

API_ERRORS = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
    500: InternalServerError
}

def _program_close_session(session: ClientSession):
    if not session.closed:
        asyncio.get_event_loop().run_until_complete(session.close())

def _process_bal(
    response_data: Dict[str, Any], 
    guild_id: int, 
    bucket: str
) -> UserBalance:
    """Processes a user's balance. This simply puts response data into a dataclass.
    
    Parameters
    ----------
    response_data: Dict[:class:`str`, :class:`Any`]
        Data in a dictionary contaning information on the user's balance.
    guild_id: :class:`int`
        The guild's ID.

    Returns
    -------
    :class:`UserBalance`
        A dataclass containing information on the user's balance.
    """

    response_data.update({'guild_id': guild_id, 'bucket': bucket})
    response_data.pop('found', None)

    return UserBalance(**response_data)

def _process_leaderboard(
    users: dict, 
    guild_id: int, 
    bucket: str
) -> List[UserBalance]:
    """Processes a guild's leaderboard. This is simply a list of :class:`UserBalance`.
    
    .. Parameters
    .. ----------
    
    Returns
    -------
    List[:class:`UserBalance`]
        A list of dataclasses containing information on each user's balance.
    """

    return [_process_bal(user, guild_id, bucket) for user in users]

def _check_bal_args(
    cash: Optional[Union[int, str]] = None, 
    bank: Optional[Union[int, str]] = None, 
    reason: Optional[str] = None
) -> bool:
    """Checks types and content of arguments before editing or patching a user's balance.
    
    Parameters
    ----------
    cash: Union[:class:`int`, :class:`str`]
        Amount to set the user's cash amount to. If this is a :class:`str`, it must be set to "Infinity".
    bank: Union[:class:`int`, :class:`str`]
        Amount to set the user's bank amount to. If this is a :class:`str`, it must be set to "Infinity".
    reason: str
        The reason as to why the user's balance was modified.
    
    Raises
    ------
    ValueError
        You did not specify an :class:`int` or "Infinity" for the ``cash`` and/or ``bank`` parameter.

    Returns
    -------
    :class:`bool`
        Returns ``True`` only if all checks have passed.
    """

    if cash is None and bank is None:
        raise ValueError('an int or "Infinity" must be specified for either cash or bank')

    for arg in (d := {'cash': cash, 'bank': bank}):
        value = d[arg]
        if value is None:
            continue
        else:
            if (t := type(value)) not in [int, str]:
                raise TypeError(f"{arg} can only be int or str but was {t}")
                
            elif t is str and value not in ['Infinity', '-Infinity']:
                raise ValueError(f'when {arg} is a str, it has to be "Infinity" but "{value}" was received')

    if reason and (t := type(reason)) is not str:
        raise TypeError(f'reason can only be str but was "{t}"')

    return True

class UnbeliClient:
    """
    The client to interact with UnbelievaBoat's API.

    Parameters
    ---------
    token: :class:`str`
        The Authorization token which will be used when requesting data.
    prevent_rate_limits: Optional[:class:`bool`]
        Whether the client will sleep through ratelimits to prevent 429 errors. This defaults to ``True``.
    retry_rate_limits: Optional[:class:`bool`]
        Whether the client will sleep and retry after 429 errors. This defaults to ``False``.
    session: Optional[:class:`aiohttp.ClientSession`]
        An open ClientSession which will be used throughout to request with.
        If this is ``None``, a new ClientSession will be opened.

    Attributes
    ----------
    rate_limits: :class:`ClientRateLimits`
        Dictionary containing information on the rate limit status of the client in the API.

        +---------------------------+--------------------------------------------------------------------------+
        |         Key name          |                         Description                                      |
        +===========================+==========================================================================+
        | ``X-RateLimit-Limit``     | The number of requests that can be made.                                 |
        +---------------------------+--------------------------------------------------------------------------+
        | ``X-RateLimit-Remaining`` | The number of remaining requests that can be made.                       |
        +---------------------------+--------------------------------------------------------------------------+
        | ``X-RateLimit-Reset``     | Datetime to when the rate limit resets.                                  |
        +---------------------------+--------------------------------------------------------------------------+
        | ``retry_after``           | The number of seconds to wait before being able to make another request. |
        +---------------------------+--------------------------------------------------------------------------+
    """

    _BASE_URL = API_BASE_URL

    def __init__(
        self,
        token: str,
        *,
        prevent_rate_limits: Optional[bool] = True,
        retry_rate_limits: Optional[bool] = False,
        session: Optional[ClientSession] = None
    ) -> None:
        self._headers: Dict[str, Any] = {
            "Accept": "application/json",
            'Authorization': token
        }
        self._prevent_rate_limits: bool = prevent_rate_limits
        self._retry_rate_limits: bool = retry_rate_limits
        self._session: Union[ClientSession, None] = session

        self.rate_limits: ClientRateLimits = ClientRateLimits(prevent_rate_limits=prevent_rate_limits)
    
    async def close_session(self) -> None:
        """Closes the current session."""
        if self._session and isinstance(self._session, ClientSession) and not self._session.closed:
            await self._session.close()

    async def get_permissions(
        self, 
        guild_id: int
    ) -> int:
        """
        Returns the application's permissions for the specified guild's ID.

        Parameters
        ----------
        guild_id: :class:`int` 
            The target guild's ID.

        Raises:
        TypeError
            You did not pass an ``int`` to the ``guild_id`` parameter.
        Unauthorized
            The wrong Application Token was passed.
        NotFound
            You provided an invalid guild ID.

        Returns
        -------
        :class:`int`
            ...
        """
        if (t := type(guild_id)) is not int:
            raise TypeError(f"guild_id must be an int but {t} was received")

        method = 'GET'
        path = f'/applications/@me/guilds/{guild_id}'
        bucket = method + path

        return await self._request(method, path, bucket)

    async def get_guild(
        self, 
        guild_id: int
    ) -> Guild:
        """
        Retrieves a guild from the API.

        Parameters
        ----------
        guild_id: :class:`int`
            The target guild's ID.
    
        Raises
        ------
        NotFound
            You provided an invalid guild ID.

        Returns
        -------
        :class:`Guild`
            A dataclass containing information on the retrieved guild.
        """

        if (t := type(guild_id)) is not int:
            raise TypeError(f"guild_id must be an int but {t} was received")

        method = 'GET'
        path = f"/guilds/{guild_id}"
        bucket = method + path

        return await self._request(method, path, bucket)

    async def get_guild_leaderboard(
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

        Parameters
        ----------
        guild_id: :class:`int` 
            The target guild's ID.
        sort: :class:`str` 
            Sort the leaderboard by "cash", "bank" or "total".
        limit: :class:`int` 
            Limit the amount of users to retrieve.
        offset: :class:`int` 
            retrieve users only from said place and below in the leaderboard
        page: :class:`int` 
            page number to retrieve
            if specified returns a dictionary containing the list of user's leaderboard under key 'users' and
            additional 'page' with the current page and 'total_pages' with number available pages.
        
        Raises
        ------
        TypeError
            You specified both ``offset`` and ``page``.
        ValueError
            You specified something other than "cash", "bank" or "total" for ``sort``.
        Unauthorized
            The wrong Application Token was passed.
        NotFound
            You provided an invalid guild ID.

        Returns:
            Union[List[:class:`UserBalance`], [Dict[:class:`str`, Union[:class:`int`, List[:class:`Userbalance`]]]]]
                Dictionary containing leaderboard information.
        """

        if offset and page:
            raise TypeError('offset cannot be used with the page parameter')

        params: Optional[List[str]] = []

        if sort is not None:
            if (t := type(sort)) is not str:
                raise TypeError(f'sort must be type str but was "{t}"')
            elif sort not in ['cash', 'bank', 'total']:
                raise ValueError(f'sort can only be "cash", "bank" or "total" but was "{sort}"')
            else:
                params.append(f"sort={sort}")

        for arg in (d := {'limit': limit, 'offset': offset, 'page': page}):
            if d[arg] is not None:
                if (t := type(d[arg])) is not int:
                    raise TypeError(f'{arg} can only be type int but was {t}')
                else:
                    params.append(f"&{arg}={d[arg]}")

        method = 'GET'
        base_path = f'/guilds/{guild_id}/users'

        query_path = base_path + "".join(params)
        bucket = method + base_path

        return await self._request(
            method, 
            query_path, 
            bucket, 
            guild_id=guild_id, 
            page=page
        )

    async def get_user_balance(
        self, 
        guild_id: int, 
        user_id: int
    ) -> UserBalance:
        """
        Retrieves a user's balance.

        Parameters
        ----------
        guild_id: :class:`int` 
            The guild's ID which the user belongs to.
        user_id: :class:`int` 
            The user's ID. 
        
        Raises
        ------
        Unauthorized
            The wrong Application Token was passed.
        NotFound
            You provided an invalid guild, and/or user ID.

        Returns
        -------
        :class:`UserBalance`
            A dataclass containing information on the retrieved user's balance.
        """

        for arg in (d := {'guild_id': guild_id, 'user_id': user_id}):
            if (t := type(d[arg])) is not int:
                raise TypeError(f"{arg} can only be int but was {t}")

        method = 'GET'
        path = f"/guilds/{guild_id}/users/{user_id}"
        bucket = method + path

        return await self._request(method, path, bucket, guild_id=guild_id)

    async def edit_user_balance(
        self,
        guild_id: int,
        user_id: int,
        cash: Optional[Union[int, str]] = None,
        bank: Optional[Union[int, str]] = None,
        reason: Optional[str] = None
    ) -> UserBalance:
        """
        Increase or decrease the user's balance by a value given in the params.
        To decrease the balance, provide a negative number.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild's ID which the user belongs to.
        user_id: :class:`int`
            The user's ID.
        cash: Optional[Union[:class:`int`, :class:`str`]]
            Amount to modify the user's cash amount to. If this is a :class:`str`, it must be set to "Infinity".
        bank: Optional[Union[:class:`int`, :class:`str`]]
            Amount to modify the user's bank amount to. If this is a :class:`str`, it must be set to "Infinity".
        reason: Optional[:class:`str`]
            The reason to why the balance was modified. 

        Raises
        ------
        Unauthorized
            The wrong Application Token was passed.
        Forbidden
            The Application is not authorized to perform this action.
        NotFound
            You provided an invalid guild, and/or user ID.

        Returns
        -------
        :class:`UserBalance`
            A dataclass containing information on the user's newly modified balance.
        """

        check = _check_bal_args(cash, bank, reason)
        if check:
            data: Dict[str, Any] = {
                'cash': cash, 
                'bank': bank, 
                'reason': reason
            }

            method = 'PATCH'
            path = f"/guilds/{guild_id}/users/{user_id}"
            bucket = method + path
            return await self._request(method, path, bucket, guild_id=guild_id, data=dumps(data))

    async def set_user_balance(
        self,
        guild_id: int,
        user_id: int,
        cash: Optional[Union[int, str]] = None,
        bank: Optional[Union[int, str]] = None,
        reason: Optional[str] = None
    ) -> UserBalance:
        """
        Sets a user's balance to a given amount.
        At least one of cash, or bank must be specified.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild's ID which the user belongs to.
        user_id: :class:`int`
            The user's ID.
        cash: Optional[Union[:class:`int`, :class:`str`]]
            Amount to set the user's cash amount to. If this is a :class:`str`, it must be set to "Infinity".
        bank: Optional[Union[:class:`int`, :class:`str`]]
            Amount to set the user's bank amount to. If this is a :class:`str`, it must be set to "Infinity".
        reason: Optional[:class:`str`]
            The reason to why the balance was mofified.
    
        Raises
        ------
        Unauthorized
            The wrong Application Token was passed.
        Forbidden
            The Application is not authorized to perform this action.
        NotFound
            You provided an invalid guild, and/or user ID.

        Returns
        -------
        :class:`UserBalance`
            A dataclass containing information on the user's newly modified balance.
        """

        check = _check_bal_args(cash, bank, reason)
        if check:
            data: Dict[str, Any] = {
                'cash': cash, 
                'bank': bank, 
                'reason': reason
            }

            method = 'PATCH'
            path = f"/guilds/{guild_id}/users/{user_id}"
            bucket = method + path
            return await self._request(method, path, bucket, guild_id=guild_id, data=dumps(data))

    def _get_member_url(self, guild_id: int, member_id: int) -> Tuple(str, str):
        url = self._BASE_URL + f'/guilds/{guild_id}/users/{member_id}'
        route = url[len(self._BASE_URL):-len(str(member_id))] + ':id'
        return url, route

    @staticmethod
    def _get_caller() -> stack:
        return stack()[2][3]

    def _get_bucket_handler(self, bucket: str) -> BucketHandler:
        bucket_handler = self.rate_limits.buckets.get(bucket)
        if bucket_handler is None:
            bucket_handler = self.rate_limits.buckets[bucket] = BucketHandler(bucket=bucket)
        return bucket_handler

    async def _ensure_session(self):
        """Ensures theres an open ``ClientSession``. If it does not exist or it's closed a new one is created.
        """
        if not self._session or self._session.closed:
            self._session = cs = ClientSession()
            atexit.register(_program_close_session, cs)
    
    async def generate_new_session(self, session: Optional[ClientSession] = None):
        """ Generates a new ``ClientSession`` for the client.

        Parameters
        ----------
        session Optional[:class:`ClientSession`]
            The session to use with the client.
        """
        await self.close_session()
        self._session = cs = session or ClientSession()
        atexit.register(_program_close_session, cs)
    
    def __del__(self):
        asyncio.get_event_loop().run_until_complete(self.close_session())

    async def _request(
        self,
        method: str,
        path: str,
        bucket: str,
        data: Optional[str] = None,
        caller = None,
        guild_id: Optional[int] = None,
        page: Optional[int] = None
    ) -> Any:
        """
        Processes requests to the Unbelievaboat's API.

        Parameters
        ----------
        method: :class:`str`
            The method used for the request, can be 'PUT', 'PATCH' or 'GET'.
        path: :class:`str`
            The path to request to/from.
        data: :class:`str`
            Data which will be used for the request. This has to be a ``str``.
        guild_id: Optional[:class:`int`]
            The guild's ID.
        page: Optional[:class:`int`]
            Number of pages in the leaderboard to retrieve from the API.

        Raises
        ------
        BadRequest
            ...
        Unauthorized
            The wrong Application Token was passed.
        Forbidden
            The Application is not authorized to perform this action.
        NotFound
            The wrong data was passed, leading to an unknown endpoint.
        TooManyRequests
            You got ratelimited - too many requests were sent.
        InternalServerError
            ...
        """

        url = self._BASE_URL + path
        headers = self._headers

        # method_types = {
        #     'PUT': self._session.put(url=url, data=data),
        #     'PATCH': self._session.patch(url=url, data=data),
        #     'GET': self._session.get(url=url)
        # }
        method_types = ['PUT', 'PATCH', 'GET']
        if method not in method_types:
            raise ValueError("method must be either PUT, PATCH or GET")

        if caller is None:
            caller = self._get_caller()

        bucket_handler: BucketHandler = self._get_bucket_handler(bucket)
        bucket_handler.prevent_429 = self._prevent_rate_limits

        await self._ensure_session()

        async with self.rate_limits.global_limiter:
            async with bucket_handler as bh:
                # async with method_types[method] as response:
                async with self._session.request(method, url, headers=headers, data=data) as response:
                    bh.check_limit_headers(response)  # sets up the bucket rate limit attributes with response headers
                    response_data: Dict[str, Any] = await response.json()

                try:
                    if await self._check_response(response=response, bucket=bucket):

                        if caller in ['set_user_balance', 'set_user_balance', 'get_user_balance']:
                            return _process_bal(response_data, guild_id, bucket)

                        elif caller == 'get_guild_leaderboard':
                            if page is None:
                                return _process_leaderboard(response_data, guild_id, bucket)
                            else:
                                response_data['users'] = _process_leaderboard(response_data['users'], guild_id, bucket)
                                return response_data

                        elif caller == 'get_permissions':
                            return response_data['permissions']

                        elif caller == 'get_guild':
                            response_data['bucket'] = bucket                     
                            # a change in the API adds a few empty fields to the response (vanity_code, roles and channels)
                            response_data = {
                                key: value for key, value in response_data.items()
                                if key in ['id', 'name', 'icon', 'owner_id', 'member_count', 'symbol', 'bucket']
                            }
                            return Guild(**response_data)

                except TooManyRequests as E:
                    if self._retry_rate_limits is True:
                        timeout = response_data['retry_after'] / 1000 + 1
                        await asyncio.sleep(timeout)
                        # reschedule same request
                        return await self._request(method, url, bucket, data, caller=caller, guild_id=guild_id, page=page)

                    else:
                        raise E

    async def _check_response(self, response: ClientResponse, bucket: str) -> bool:
        """Checks API response for errors. This only returns ``True`` on status code 200.
        
        Parameters
        ----------
        response: :class:`aiohttp.ClientResponse`
            The response received from a HTTP request.
        bucket: str
            ...
        """

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
                raise UnknownException(error_text)
