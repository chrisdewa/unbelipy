# -*- coding: utf-8 -*-
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

from dataclasses import (
    dataclass, 
    field
)
from typing import (
    Optional,
    Union, 
    List, 
    Any
)

__all__ = (
    "UserBalance",
    "Guild"
)

@dataclass(order=True)
class UserBalance:
    """
    Dataclass representing the balance of a user from the API.

    .. note::
        The ``total``, ``bank`` and ``cash`` attributes *may* be a float if set to infinity (positive or negative).

    Attributes
    ----------
    total: Union[:class:`int`, :class:`float`]
        The user's total amount of money (cash + bank).
    bank: Union[:class:`int`, :class:`float`]
        The user's bank amount.
    cash: Union[:class:`int`, :class:`float`]
        The user's cash amount.
    user_id: :class:`int`
        The user's unique ID.
    guild_id: :class:`int`
        The user's guild's unique ID.
    rank : :class:`int`
        The rank of the user in the guild according to query parameters.
    """

    total: Union[int, float]
    cash: Union[int, float] = field(compare=False)
    bank: Union[int, float] = field(compare=False)
    user_id: int = field(compare=False)
    guild_id: int = field(compare=False)
    bucket: str = field(compare=False)
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
            setattr(self, 'rank', int(self.rank))

    def __repr__(self):
        return (
            f"UserBalance(total={self.total}, cash={self.cash}, bank={self.bank}, rank={self.rank}, "
            f"user_id={self.user_id}, guild_id={self.guild_id})"
        )

@dataclass
class Guild:
    """
    Dataclass representing a guild from the API.

    Attributes
    ----------
        id: :class:`int`
            The guild's unique ID.
        name: :class:`str`
            The guild's name.
        owner_id: :class:`int`
            The guild owner's unique ID.
        member_count: :class:`int`
            The guild's amount of members.
        symbol: :class:`str`
            The guild's currency symbol.
    """

    id: int
    name: str = field(compare=False)
    icon: str = field(compare=False)
    owner_id: int = field(compare=False)
    member_count: int = field(compare=False)
    symbol: str = field(compare=False)
    bucket: str = field(compare=False)

    # don't document
    channels: Optional[List[Any]] = field(compare=False, default_factory=[])
    roles: Optional[List[Any]] = field(compare=False, default_factory=[])

    def __post_init__(self):
        self.id = int(self.id)
        self.owner_id = int(self.owner_id)
