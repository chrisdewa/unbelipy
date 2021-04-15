# -*- coding: utf-8 -*-
"""
Module to facilitate integration with UnbelievaBoat's API
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, Dict, List, Any, Optional

from aiohttp import ClientSession, ClientResponse

from unbelipy.errors import TooManyRequests, NotFound, api_errors, UnknownError

UNB_API_VERSION = 'v1'


@dataclass(order=True)
class Balance:
    """
    Dataclass containing the balance status of the specified member
    Attributes:
        total: total amount of currency (cash + bank)
        bank: amount in bank
        cash: amount in cash
        user_id: id of the user for which the amount is set
        guild_id: id for the guild the user belongs to
        rank: rank of the user in the guild according to query parameters
    Comparisons:
        Comparisons are made only with "total"
        Supported operations:
            __eq__ (==)
            __lt__ (<)
            __le__ (<=)
            __gt__ (>)
            __ge__ (>=)
    Notes:
        Amounts in total, bank and cash can be float if set to infinity (positive or negative)
    """
    total: Union[int, float]
    cash: Union[int, float] = field(compare=False)
    bank: Union[int, float] = field(compare=False)
    user_id: int = field(compare=False)
    guild_id: int = field(compare=False)
    rank: int = field(compare=False, default=None)

    def __post_init__(self):
        for attr in ['cash', 'bank', 'total']:
            value = getattr(self, attr)
            try:
                value = int(value)
            except ValueError:
                d = {'Infinity': float('inf'), '-Infinity': float('-inf')}
                value = d[value]
            finally:
                setattr(self, attr, value)

        for attr in ['user_id', 'guild_id']:
            value = getattr(self, attr)
            setattr(self, attr, int(value))

        if self.rank is not None:
            self.rank = int(self.rank)

    def __repr__(self):
        return f"Balance(total={self.total}, user_id={self.user_id}, guild_id={self.guild_id})"


@dataclass
class UnbGuild:
    """
    Dataclass with guild information. 
    Comparisons are made only with member_count
    """
    id: int = field(compare=False)
    name: str = field(compare=False)
    icon: str = field(compare=False)
    owner_id: int = field(compare=False)
    member_count: int
    symbol: str = field(compare=False)
    channels: List[Any] = field(compare=False, default_factory=[])
    roles: List[Any] = field(compare=False, default_factory=[])

    def __post_init__(self):
        self.id = int(self.id)
        self.owner_id = int(self.owner_id)


def _dict_to_bal(bal_dict: dict) -> Balance:
    processed = {k: v for k, v in bal_dict.items() if k != 'found'}  # get_balance returns redundant 'found' field
    return Balance(**processed)


def _check_bal_args(cash, bank, reason):
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
            elif t is str and value != 'Infinity':
                raise ValueError(f'When {arg} is a String "Infinity" is expected but "{value}" was received')
    if (t := type(reason)) is not str:
        raise TypeError(f'Reason can only be str but was "{t}"')
    return True


class UnbeliClient:
    """
    Client Class to interact with Unbelievaboat's API
    Public Attributes:
        rate_limit_data:
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
    rate_limit_data: Dict[str, Union[str, int, float, datetime, None]] = {
        'X-RateLimit-Limit': None,
        'X-RateLimit-Remaining': None,
        'X-RateLimit-Reset': None,
        'retry_after': None
    }
    _base_url = 'https://unbelievaboat.com/api/' + f'{UNB_API_VERSION}'
    _member_url = _base_url + '/guilds/{guild_id}/users/{member_id}'

    def __init__(self, token: str):
        self._header = {'Authorization': token}

    async def _balance_from_response(self, response: ClientResponse, guild_id: int):
        """Checks API errors before returning a response object via _dict_to_bal"""
        if await self._check_response(response):
            data = await response.json()
            data['guild_id'] = guild_id
            return _dict_to_bal(data)

    async def _check_response(self, response: ClientResponse):
        """Checks API response for errors. Returns True only on status 200"""
        status = response.status
        reason = response.reason
        data = await response.json()

        for key in ['X-RateLimit-Limit',
                    'X-RateLimit-Remaining',
                    'X-RateLimit-Reset']:
            value = response.headers.get(key)
            if value is not None:
                value = int(value)
                if key == 'X-RateLimit-Reset':
                    value = datetime.utcfromtimestamp(value / 1000)
            self.rate_limit_data[key] = value
        if type(data) is dict:
            retry_after = data.get('retry_after')
            if retry_after is not None:
                retry_after = int(
                    retry_after) / 1000 + 1  # sometimes following this rate limit still results in 429 so adding 1
                                             # solves it.
            self.rate_limit_data['retry_after'] = retry_after

        if status == 200:
            return True
        elif status == 429:
            message = data['message']
            if 'global' in data:
                text = f"Global rate limit. {data['message']}"
            elif 'retry_after' in data:
                text = f"{message} retry after: {(data['retry_after']) / 1000}s"
            else:
                text = f"{message}"
            raise TooManyRequests(text)
        elif status == 404:
            raise NotFound(f'Error Code: "{status}" Reason: "{reason}"')
        else:
            error_text = f'Error code: "{status}" Reason: "{reason}"'
            if status in api_errors:
                raise api_errors[status](error_text)
            else:
                raise UnknownError(error_text)

    def __get_member_url(self, guild_id: int, member_id: int):
        return self._member_url.format(guild_id=guild_id, member_id=member_id)

    async def guild_permissions(self, guild_id: int) -> int:
        """
        Returns the application's permissions for the guild with specified id
        """
        if (t := type(guild_id)) is not int:
            raise TypeError(f"guild_id must be an int but {t} was received")

        url = f"{self._base_url}/applications/@me/guilds/{guild_id}"
        async with ClientSession(headers=self._header) as cs:
            async with cs.get(url=url) as r:
                if await self._check_response(r):
                    data = await r.json()
                    return data['permissions']

    async def get_guild(self, guild_id) -> UnbGuild:
        """
        Args:
            guild_id: id of the target guild

        Returns:
            Returns a dataclass for the target guild with the following attributes:
                id (str)
                name (str)
                icon (str: icon hash)
                owner_id (str)
                member_count (int)
                symbol (str) currency symbol
        """
        if (t := type(guild_id)) is not int:
            raise TypeError(f"guild_id must be an int but {t} was received")

        url = f"{self._base_url}/guilds/{guild_id}"
        async with ClientSession(headers=self._header) as cs:
            async with cs.get(url=url) as r:
                if await self._check_response(r):
                    data = await r.json()
                    return UnbGuild(**data)

    async def get_balance(self, guild_id: int, member_id: int) -> Balance:
        """
        Args:
            guild_id: id of the guild the member belongs to
            member_id: id of the member
        Returns:
            balance (Balance) A dataclass containing the member's balance
        """
        for arg in (d := {'guild_id': guild_id, 'member_id': member_id}):
            if (t := type(d[arg])) is not int:
                raise TypeError(f"{arg} can only be int but was {t}")

        url = self.__get_member_url(guild_id, member_id)
        async with ClientSession(headers=self._header) as cs:
            async with cs.get(url) as r:
                return await self._balance_from_response(r, guild_id)

    async def edit_balance(self,
                           guild_id: int,
                           member_id: int,
                           cash: Union[int, str] = 0,
                           bank: Union[int, str] = 0,
                           reason: str = '') -> Balance:
        """
        Increase or decrease the Member's balance by a value given in the params.
        To decrease the balance, provide a negative number.

        Args:
            guild_id: id of the guild the member belongs to
            member_id: id of the member
            cash: Amount to modify the member's cash amount
            bank: Amount to modify the member's bank amount
            reason: specifies the reason why the balance was modified

        Returns:
            balance (Balance) a dataclass containing the information of the newly modified balance for the user.


        """
        url = self.__get_member_url(guild_id, member_id)

        if _check_bal_args(cash, bank, reason):
            data = {'cash': cash, 'bank': bank, 'reason': reason}
            async with ClientSession(headers=self._header) as cs:
                async with cs.patch(url, data=json.dumps(data)) as r:
                    return await self._balance_from_response(r, guild_id=guild_id)

    async def set_balance(self,
                          guild_id: int,
                          member_id: int,
                          cash: Union[int, str, None] = None,
                          bank: Union[int, str, None] = None,
                          reason: str = '') -> Balance:
        """
        Set the Member's balance to the given params.
        Args:
            guild_id: id of the guild the member belongs to
            member_id: id of the member
            cash: sets the member's cash amount
            bank: sets the member's bank amount
            reason: specifies the reason why the balance was modified
        Usage Notes:
            if cash and/or bank is a string they must be "Infinite".
            At least cash or bank are needed
        Returns:
            balance (Balance) a dataclass containing the information of the newly set balance for the user.
        """

        url = self.__get_member_url(guild_id, member_id)

        if _check_bal_args(cash, bank, reason):
            data = {'cash': cash, 'bank': bank, 'reason': reason}
            async with ClientSession(headers=self._header) as cs:
                async with cs.put(url, data=json.dumps(data)) as r:
                    return await self._balance_from_response(r, guild_id)

    async def get_leaderboard(self,
                              guild_id: int,
                              sort: Optional[str] = None,
                              limit: Optional[int] = None,
                              offset: Optional[int] = 1,
                              page: Optional[int] = None
                              ) -> Union[List[Balance],
                                         Dict[str, Union[int,
                                                         List[Balance]]]]:
        """
        Retrieves leaderboard information for a guild
        Args:
            guild_id (int): id of the guild
            sort (str): pass 'cash', 'bank' or 'total' to sort accordingly
            limit (int): amount of users to retrieve
            offset (int): retrieve users only from set place and below in the leaderboard
            page (int): page number to retrieve
                if specified returns a dictionary containing the list of user's leaderboard under key 'users' and
                additional 'page' with the current page and 'total_pages' with number available pages.
        Returns:
            dictionary containing leaderboard information
        """

        url = self._base_url + f'/guilds/{guild_id}/users?'
        if sort is not None:
            if (t := type(sort)) is not str:
                raise TypeError(f'sort must be type str but was "{t}"')
            elif sort not in ['cash', 'bank', 'total']:
                raise ValueError(f'Sort can only be "cash", "bank" or "total" but was "{sort}"')
            else:
                url += f"sort={sort}&"

        for arg in (d := {'limit': limit, 'offset': offset, 'page': page}):
            if d[arg] is not None:
                if (t := type(d[arg])) is not int:
                    raise TypeError(f'{arg} can only be type int but was {t}')
                else:
                    url += f"{arg}={d[arg]}&"

        url = url[:-1]

        def process_lb(lb_dict: dict):
            for user in lb_dict:
                user['guild_id'] = guild_id
            return [_dict_to_bal(user) for user in lb_dict]

        async with ClientSession(headers=self._header) as cs:
            async with cs.get(url=url) as r:
                if await self._check_response(r):
                    data = await r.json()
                    if page is None:
                        return process_lb(data)
                    else:
                        data['users'] = process_lb(data['users'])
                        return data
