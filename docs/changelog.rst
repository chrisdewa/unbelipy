.. currentmodule:: unbelipy

Changelog
=========

This page outlines the changes in specific versions.
Some *may* be breaking changes, which requires you to update your code as soon as possible.

v1.2.0b
-------
- Bucket routes edited. Mainly user balance GET/PATCH/PUT and leaderboard.
- Fixed bug in :attr:`UnbeliClient.retry_rate_limits`

v1.1.1b
-------
- Moved the rate limit throttler for buckets from the exit component of the context manager to enter, after acquiring the lock .

v1.1.0b
-------
- Rewritten rate limit handlers. :attr:`Client.rate_limits` now holds a ``buckets`` attribute, which is a dictionary containing the name of the bucket as key and its handler as the value. 
    - Bucket handlers are classes that hold specific bucket rate limit information updated with each request, and a context manager that throttles requests to prevent ``429``\s if that's enabled.  
    - ``True`` concurrency is only possible at the moment with different buckets.

- Dataclasses now contain an attribute "bucket" with the name of the bucket that produced the dataclass.
    - This is useful to get the bucket handler from :attr:`UnbeliClient.rate_limits.buckets`
- Next patch is expected to finally resolve rate_limit functionality

v1.0.4b
-------
- Fixed bug with :meth:`ClientRateLimits.currently_limited` from :issue:`6`

v1.0.1b
-------
- Documentation improvements.
- Versioning reformatting to follow semantic conventions.
- Added Balance string representation information.

v0.0.1b
-------
- Finally in beta from alpha.
- Improved README.md
- Adjusted rate limit prevention parameters.
- Added MIT License.

v0.0.9a
-------
- Specific route rate limits now managed by semaphore set up after first request.
- Probably the last version of alpha

v0.0.8a
-------
- Renamed ``Client.rate_limit_data`` to :attr:`Client.rate_limits`
- Correctly handles global limit by waiting until cleared. Tested on concurrent spammed tasks. For this it uses `aiolimiter <https://github.com/mjpieters/aiolimiter>`
    - `Client.rate_limits.global_limiter` is an async context manager to throttle requests to the API if :attr:`Client.prevent_rate_limits` is ``True``
- Specific route rate limits are also now handled by waiting for response headers and adjusting speed to prevent 429s
- For now `aiolimiter <https://github.com/mjpieters/aiolimiter>` is a requiered dependency might change in the future

v0.0.7a
-------
- All client api interaction methods are now executed with `Client._request` which handles rate limits
- Rate limits are now prevented only in non concurrent (massive calls with asyncio.gather will still fail).
- added client parameters to decrease possibility of hitting 429s and retrying if it happens.

v0.0.6a
-------
- Modified ``UnbeliClient.rate_limit_data``. 
    - It now holds a class which attributes hold rate limit data in a per bucket basis.
- Added this changelog
