[![PyPI status](https://img.shields.io/pypi/status/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI version fury.io](https://badge.fury.io/py/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI license](https://img.shields.io/pypi/l/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)

# unbelip

Asynchronous wrapper for UnbelievaBoat's API written in python

# Characteristics
- Easy to use
- Full error handling
- Type hinted and readable code

# Project status
Early alpha and as such unsuitable for production.

# Installation

`pip install unbelipy`

# Use:

```python
from unbelipy import UnbeliClient
import asyncio
TOKEN = "Token generated through Unbelievaboat's portal"

client = UnbeliClient(token=TOKEN)

async def main():
    # get guild information
    guild_info = await client.get_guild(guild_id=305129477627969547)
    
    # get guild leaderboard
    guild_leaderboard = await client.get_leaderboard(guild_id=305129477627969547)
    
    # get user balance
    balance = await client.get_balance(guild_id=305129477627969547, member_id=80821761460928512)
    
    # put balance (set to x amount)
    balance = await client.set_balance(guild_id=305129477627969547, 
                                       member_id=80821761460928512,
                                       cash=1000,
                                       reason="Showing off put method")
    # patch balance (increment or decrement by x amount)
    balance = await client.edit_balance(guild_id=305129477627969547, 
                                       member_id=80821761460928512,
                                       cash=-500,
                                       reason="Showing off patch method")
```

"balance" is a returned Dataclass with balance information containing:
- total: total amount of currency (cash + bank)
- bank: amount in bank
- cash: amount in cash
- user_id: id of the user for which the amount is set
- guild_id: id for the guild the user belongs to
- rank: rank of the user in the guild according to query parameters

"guild_info" is a dataclass with guild info containing:
- id
- name 
- icon
- owner_id  
- member_count  
- symbol (currency)

UnbeliClient also has a rate_limit_data attribute with information returned with each request from the API.


