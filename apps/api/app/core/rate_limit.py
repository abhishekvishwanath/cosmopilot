import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status


class _Bucket:
    __slots__ = ("hits",)

    def __init__(self) -> None:
        self.hits: deque[float] = deque()


_buckets: dict[str, _Bucket] = defaultdict(_Bucket)


def rate_limit(max_requests: int, window_seconds: int) -> Callable[[Request], Awaitable[None]]:
    """
    Per-IP fixed-window limiter for public, unauthenticated endpoints
    (CLAUDE.md §23/§28). In-process memory only — fine for a single API
    instance; swap for a Redis-backed limiter (docs/PROVIDER_INTERFACES.md)
    before running multiple replicas, since counts don't share across them.
    """

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = _buckets[client_ip]
        while bucket.hits and now - bucket.hits[0] > window_seconds:
            bucket.hits.popleft()
        if len(bucket.hits) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests. Please slow down.",
                        "details": {},
                    }
                },
            )
        bucket.hits.append(now)

    return _dependency
