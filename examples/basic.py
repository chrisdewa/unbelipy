import asyncio

from unbelipy import UnbeliClient

UNB_API_TOKEN = "Token generated from https://unbelievaboat.com/applications/"

# Warning:
# It's advisable that you set your token as an enviromental variable. 
# Always keep your credentials as a secret.

unbeliclient = UnbeliClient(token=UNB_API_TOKEN)
# Note:
# It is recommended to instantiate the client with 
# prevent_rate_limits set to True with or without `rety_rate_limits`.
# Performance is similar either ways but having `retry_rate_limits` set to True may result in multiple 429 errors.

guild_id = 693980879181053994 
member_id = 365957462333063170

async def main() -> None:
    # GET guild information
    guild_info = await unbeliclient.get_guild(guild_id)
    print(f"Guild Information: ", guild_info)

    # GET guild leaderboard
    guild_leaderboard = await unbeliclient.get_guild_leaderboard(guild_id)
    print(f"Guild leaderboard: ", guild_leaderboard)

    # GET user balance
    user_balance = await unbeliclient.get_user_balance(
        guild_id=guild_id, 
        user_id=member_id
    )
    print(f"User balance: ", user_balance)

    # PATCH user balance (increase/decrease values)
    edited_balance = await unbeliclient.edit_user_balance(
        guild_id=guild_id, 
        user_id=member_id,
        cash=500,
        reason="showing off PATCH method"
    )
    
    print(f"Edited user balance: ", edited_balance)

    # PUT user balance (set to xxx value)
    new_balance = await unbeliclient.set_user_balance(
        guild_id=guild_id,
        user_id=member_id,
        cash=-500,
        reason="showing off PUT method"
    )
    print("After setting balance: ", new_balance)

    
    print('closing session')
    await unbeliclient.close_session() # important to exit cleanly



asyncio.run(main())

# Now that we're done with stuff, we should close the session.
