import asyncio

from unbelipy import UnbeliClient

UNB_API_TOKEN = "Token generated from https://unbelievaboat.com/applications/"
# Warning:
# It is advisable to keep your token safely
# .env files are an option but it requires another dependency, so it's not always warranted.

unbeliclient = UnbeliClient(
    token=UNB_API_TOKEN
)
# Note:
# It is recommended to instantiate the client with 
# prevent_rate_limits set to True with or without `rety_rate_limits`.
# Performance is similar either ways but having `retry_rate_limits` set to True may result in multiple 429 errors.

async def main() -> None:
    # GET guild information
    guild_info = await unbeliclient.get_guild(305129477627969547)
    print(f"Guild Information: ", guild_info)

    # GET guild leaderboard
    guild_leaderboard = await unbeliclient.get_guild_leaderboard(305129477627969547)
    print(f"Guild leaderboard: ", guild_leaderboard)

    # GET user balance
    user_balance = await unbeliclient.get_balance(
        guild_id=305129477627969547, 
        member_id=80821761460928512
    )
    print(f"User balance: ", user_balance)

    # PATCH user balance (increase/decrease values)
    edited_balance = await unbeliclient.edit_user_balance(
        guild_id=305129477627969547, 
        member_id=80821761460928512,
        cash=500,
        reason="showing off PATCH method"
    )
    print(f"Edited user balance: ", edited_balance)

    # PUT user balance (set to xxx value)
    new_balance = await unbeliclient.set_user_balance(
        guild_id=305129477627969547,
        member_id=80821761460928512,
        cash=-500,
        reason="showing off PUT method"
    )
    print("After setting balance: ", new_balance)

asyncio.run(main())
