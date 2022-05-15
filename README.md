# unbelipy

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![PyPI status](https://img.shields.io/pypi/status/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI version fury.io](https://badge.fury.io/py/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI downloads](https://img.shields.io/pypi/dm/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI license](https://img.shields.io/pypi/l/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)

Asynchronous wrapper for UnbelievaBoat's API written in python

---
## Characteristics
- Easy to use
- Full error handling
- Type hinted readable code
- Active maintenance
- Fully Asynchronous

---
## Note
This wrapper has not been declared to be official by the UnbelievaBoat developers. Any internal library issues/feature requests are to be directed here.

---
## Project status
Early beta stage. It's not yet production ready.  
Although most of the functionality is operational, rate limits are still being worked on.  

---
## Installation
**Python 3.8 or above required, due to typehinting.**

To install unbelipy from PyPI, use the following command:  
```sh
pip install -U unbelipy
```

Or to install from Github:  
```sh
pip install -U git+https://github.com/chrisdewa/unbelipy/
```

---
## Dependencies
The following libraries will be needed and automatically installed with unbelipy:  
- [aiohttp](https://github.com/aio-libs/aiohttp/) - async requests
- [aiolimiter](https://github.com/mjpieters/aiolimiter/) - implementation of async rate limiter

---
## Feature Requests
For feature requests, please [open a Pull Request](https://github.com/chrisdewa/unbelipy/pulls) with detailed instructions.  
Likewise, if you encounter any issues, you may [create a new Issue](https://github.com/chrisdewa/unbelipy/issues).


---
## Examples
```python
import asyncio

from unbelipy import UnbeliClient
UNB_TOKEN = "Token generated from: https://unbelievaboat.com/applications/"

client = UnbeliClient(
	token=UNB_TOKEN
)

async def main() -> None:
    # GET guild information
    guild_info = await client.get_guild(
		guild_id=305129477627969547
	)
    print(guild_info)

    # GET guild leaderboard
    guild_leaderboard = await client.get_leaderboard(
		guild_id=305129477627969547
	)
    print(guild_leaderboard)

    # GET user balance
    balance = await client.get_balance(
		guild_id=305129477627969547, member_id=80821761460928512
	)
    print(balance)

    # PUT balance (set to x amount)
    balance = await client.set_balance(
		guild_id=305129477627969547, 
        member_id=80821761460928512,
        cash=1000,
        reason="Showing off PUT method"
	)

    # PATCH balance (increment or decrement by x amount)
    balance = await client.edit_balance(
		guild_id=305129477627969547, 
        member_id=80821761460928512,
        cash=-500,
        reason="Showing off PATCH method"
	)
    print(balance)

asyncio.run(main())
```

---
## Contact
As of now, there is no support server for this library.
However, you may contact the following people on Discord:
- [ChrisDewa#4552](https://discord.com/users/365957462333063170)
- [invalid-user#1119](https://discord.com/users/714731543309844561)

<!-- #### Note:
It's recommended to use the client with `prevent_rate_limits` set to True with or without `rety_rate_limits`.
Performance is similar either way but running client with only `retry_rate_limits` may result in multiple 429 errors

------- include this using ..note or something
 -->

<!-- # Rate limit buckets examples:
- **get_guild** `'GET/guilds/{guild_id}'` 
- **get_leaderboard** `'GET/guilds/{guild_id}/users'`
- **get_balance** `'GET/guilds/{guild_id}/users/:id'`
- **edit_balance** `'PATCH/guilds/{guild_id}/users/:id'`
- **set_balance** `'PUT/guilds/{guild_id}/users/:id'`
- **get_permissions** `'GET/applications/@me/guilds/{guild_id}'` -->
  
<!-- # Know Issues:
- `'-Infinity'` is accepted by the API as a parameter for cash or bank (edit_balance and set_balance),
  but it does not appear to affect the balance. This is caused because the API receives -Infinity as null which is also 
  used when the value didn't change. At the moment there is no word this is going to be fixed.
  
------- maybe make a file in /docs for known issues -->