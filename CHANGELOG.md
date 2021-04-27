# 1.1.0b
- Rewritten rate limit handlers. client.rate_limits now holds an attribute "buckets" which is a dictionary
  that contains the name of the bucket as key and its handler as value. 
  
  Bucket handlers are classes that hold specific bucket rate limit information updated with each request, and a context manager that throttles requests to prevent 429s if that's enabled.
  
  True concurrency is only possible at the moment with different buckets.
- Dataclasses now contain an attribute "bucket" with the name of the bucket that produced the dataclass.
  This is useful to get the bucket handler from `client.rate_limits.buckets`
- Next patch is expected to finally resolve rate_limit functionality

# 1.0.4b
- Fixed bug with `currently_limited.currently_limited()` from issue #6 

# 1.0.1b - 1.0.3b 
- Documentation improvements
- Versioning reformatting to follow semantic conventions.
- Added Balance string representation information.

# 0.0.1b
- Finally in beta
- Improved README
- Adjusted rate limit prevention parameters
- Added licence (MIT)

# 0.0.9a
- specific route rate limits now managed by semaphore set up after first request
- probably the last version of alpha

# 0.0.8a
- client's attribute rate_limit_data is now rate_limits
- Correcly handles global limit by waiting until cleared. Tested on concurrent spammed tasks. for this it uses [aiolimiter](https://github.com/mjpieters/aiolimiter) 
- rate_limits.global_limit is an async context manager to throttle requests to the API if client.prevent_rate_limits is True
- specific route rate limits are also now handled by waiting for response headers and adjusting speed to prevent 429s
- For now aiolimiter is a requiered dependency, might change in the future

# 0.0.7a
- all client api interaction methods are now executed with client._request which handles rate limits
- Rate limits are now prevented only in non concurrent (massive calls with asyncio.gather will still fail).
- added client parameters to decrease possibility of hitting 429s and retrying if it happens.

# 0.0.6a
- Modified `UnbeliClient.rate_limit_data`. 
  It now holds a class which attributes hold rate limit data in a per bucket basis.
- Added this Changelog
