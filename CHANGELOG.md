# 0.0.7a
- all client api interaction methods are now executed with client._request which handles rate limits
- Rate limits are now prevented only in non concurrent (massive calls with asyncio.gather will still fail).
- added client parameters to decrease possibility of hitting 429s and retrying if it happens.

# 0.0.6a
- Modified `UnbeliClient.rate_limit_data`. 
  It now holds a class which attributes hold rate limit data in a per bucket basis.
- Added this Changelog
