
import redis
from redis.exceptions import RedisError
from fastapi import Request, HTTPException

from config.settings import settings

redis_client = redis.Redis.from_url(
    settings.REDIS_RATE_LIMIT_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)

RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])

if count == 1 then
    redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end

local ttl = redis.call('TTL', KEYS[1])

return {count, ttl}
"""


def check_login_limit(request: Request):
    ip_address = request.client.host if request.client else "unknown"

    key = f"login_limit:{ip_address}"

    try:
        count, ttl = redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            60
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Login service temporarily unavailable"
        )

    if count > 5:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(max(int(ttl), 1))}
        )
