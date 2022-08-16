.. currentmodule:: unbelipy

Getting Started
===============

Unbelipy is a simple library to interact with UmbelievaBoat's API asynchronously.

To start out generate your app token `here <https://unbelievaboat.com/applications>`_.
Don't forget to also authorize your app in your servers.

To use, first import :class:`UnbeliClient` from unbelipy and isntantiate the client with your UnbelievaBoat API's token.
The client has these public methods:

* :meth:`UnbeliClient.get_permissions` -> Returns the permissions for the app in the given server.
* :meth:`UnbeliClient.get_guild` -> Returns general info about the server.
* :meth:`UnbeliClient.get_guild_leaderboard` -> Returns the server's leadeboard.
* :meth:`UnbeliClient.get_user_balance` -> Returns the balance of a single user.
* :meth:`UnbeliClient.edit_user_balance` -> Edits the user's balances.
* :meth:`UnbeliClient.set_user_balance` -> Sets the user's balances.

Always remember to close the inner session before your program exists using :meth:`UnbeliClient.close_session` this will prevent a lot of ugly errors from unclosed client session.

.. code-block:: python
    
    client = UnbeliClient(...)
    # now use the client as you please
    ...
    # before your program exits:
    await unbeliclient.close_session()


Basic Use Example
-----------------
.. code-block:: python 
    
    from unbelipy import UnbeliClient
    UNB_API_TOKEN = "..."

    # In a coroutine
    guild_info = await unbeliclient.get_guild(guild_id)
    guild_leaderboard = await unbeliclient.get_guild_leaderboard(guild_id)
    user_balance = await unbeliclient.get_user_balance(
        guild_id=guild_id, 
        user_id=member_id
    )
    edited_balance = await unbeliclient.edit_user_balance(
        guild_id=guild_id, 
        user_id=member_id,
        cash=500,
        reason="showing off PATCH method"
    )
    new_balance = await unbeliclient.set_user_balance(
        guild_id=guild_id,
        user_id=member_id,
        cash=-500,
        reason="showing off PUT method"
    )
    await unbeliclient.close_session() # important to exit cleanly



    
   

