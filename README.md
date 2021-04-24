[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![PyPI status](https://img.shields.io/pypi/status/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI version fury.io](https://badge.fury.io/py/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI license](https://img.shields.io/pypi/l/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)

# unbelipy

Asynchronous wrapper for UnbelievaBoat's API written in python

## Characteristics
- Easy to use
- Full error handling
- Type hinted readable code

## Project status
Early beta. It's not yet production ready. 
Although most of the functionality is operational rate limits are still being worked on. 

## Installation

`pip install unbelipy`

## Use:

```python
from unbelipy import UnbeliClient
import asyncio
TOKEN = "Token generated through Unbelievaboat's portal"

client = UnbeliClient(token=TOKEN)

async def main():
    # get guild information
    guild_info = await client.get_guild(guild_id=305129477627969547)
    print(guild_info)
    # get guild leaderboard
    guild_leaderboard = await client.get_leaderboard(guild_id=305129477627969547)
    print(guild_leaderboard)
    # get user balance
    balance = await client.get_balance(guild_id=305129477627969547, member_id=80821761460928512)
    print(balance)
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
    print(balance)

asyncio.run(main())
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

### UnbeliClient init parameters:
- `token` unbelivaboat's client token.
- `prevent_rate_limits` (bool) if enabled (True, the default) the client will do its best 
  to prevent 429 type errors (rate limits). This will work even on concurrent tasts or loops.
- `retry_rate_limits` (bool) if enabled (True, default is False) the client will retry requests after 
  getting a 429 error. It will sleep through the retry_after time stipulated by UnbelivaBoat's API
  
### UnbeliClient public attributes
- `rate_limits`: this class features attributes about the state of each route. They Update after each request. 
  Bucket Attributes. Each of the following contain an async context manager to prevent 429s in case its enabled and 
  contain information about the specific route rate limit headers.
    `rate_limits.get_balance`
    `rate_limits.edit_balance`
    `rate_limits.set_balance`
    `rate_limits.get_leaderboard`
    `rate_limits.get_guild`
    `rate_limits.get_permissions`
  rate limit Methods:
    `rate_limits.currently_limited()` - returns a dictionary containing the bucket name, and a boolean indicating 
        if they're currently limited
    `rate_limits.any_limited()` - returns a bool indicating if any bucket is currently being limited
    `rate_limits.is_limited(name: str)` - returns a bool indicating if the specified bucket is being limited
  
# Know Issues:
- `'-Infinity'` is accepted by the API as a parameter for cash or bank (edit_balance and set_balance),
  but it does not appear to affect the balance. I'm waiting on the devs word on this issue.
- `client.edit_balace` which sends a patch request sometimes comes back with a 404 error even when 
  the url and data parameters are correct, even on repeated requests with the exact same data, 
  this is still being tested on.
- Rate limits are not yet functional, it is recommended to run the Client with parameters 
  `prevent_rate_limits` and `retry_rate_limits` set to `False` until they're finished. 

  
# Credits
- Currently global rate limit is handled by Martijn Pieters' [aiolimiter](https://github.com/mjpieters/aiolimiter).