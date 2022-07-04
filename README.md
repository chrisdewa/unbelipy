# unbelipy

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![PyPI status](https://img.shields.io/pypi/status/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI version fury.io](https://badge.fury.io/py/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI downloads](https://img.shields.io/pypi/dm/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)
[![PyPI license](https://img.shields.io/pypi/l/unbelipy.svg)](https://pypi.python.org/pypi/unbelipy/)

Asynchronous wrapper for UnbelievaBoat's API written in Python.

## Characteristics

- Easy to use
- Full error handling
- Type hinted readable code
- Active maintenance
- Fully Asynchronous

## Note

This wrapper has not been declared to be official by the UnbelievaBoat developers. Any internal library issues/feature requests are to be directed here.

## Project status

Early beta stage. It's not yet production ready.  
Although most of the functionality is operational, rate limits are still being worked on.  

## Installation

**Python 3.8 or above required, due to typehinting.**

To install unbelipy from PyPI, use the following command:  

```python
pip install -U unbelipy
```

Or to install from Github:  

```python
pip install -U git+https://github.com/chrisdewa/unbelipy/
```

## Dependencies

The following libraries will be needed and automatically installed with unbelipy:  

- [aiohttp](https://github.com/aio-libs/aiohttp/) - async requests
- [aiolimiter](https://github.com/mjpieters/aiolimiter/) - implementation of async rate limiter

## Feature Requests

For feature requests, please [open a Pull Request](https://github.com/chrisdewa/unbelipy/pulls) with detailed instructions.  
Likewise, if you encounter any issues, you may [create a new Issue](https://github.com/chrisdewa/unbelipy/issues).

## Examples

```python
from unbelipy import UnbeliClient

client = UnbeliClient(token='Unbelievaboats token generated from https://unbelievaboat.com/applications/')
guild_id: int = ...
member_id: int = ...

async def main():
    perms = await client.get_permissions(guild_id)
    guild = await client.get_guild(guild_id)
    guild_leaderboard = await client.get_guild_leaderboard(guild_id)
    user_balance = await client.get_user_balance(guild_id, member_id)
    user_balance = await client.edit_user_balance(guild_id, member_id, cash='5') # adds 5 to the user's cash
    user_balance = await client.set_user_balance(guild_id, member_id, cash='5') # sets the user's cash to 5
```

[More examples](https://github.com/chrisdewa/unbelipy/tree/master/examples)!

## Links

- [Documentation](https://unbelipy.readthedocs.io/en/latest/)

## Contact

As of now, there is no support server for this library.
However, you may contact the following people on Discord:

- [ChrisDewa#4552](https://discord.com/users/365957462333063170)
- [invalid-user#1119](https://discord.com/users/714731543309844561)

<!-- # Known Issues:
- `'-Infinity'` is accepted by the API as a parameter for cash or bank (edit_balance and set_balance),
  but it does not appear to affect the balance. This is caused because the API receives -Infinity as null which is also 
  used when the value didn't change. At the moment there is no word this is going to be fixed.
  
------- maybe make a file in /docs for known issues -->