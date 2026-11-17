
import json
import logging

import redis
from redis.exceptions import RedisError

from config.settings import settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    settings.REDIS_CACHE_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)

CACHE_TTL = 60
VERSION_KEY = "ecommerce:products:version"


def get_cached_products(filters: dict):
    try:
        version = redis_client.get(VERSION_KEY) or "1"

        cache_key = "products:" + json.dumps(
            {
                "version": version,
                "filters": filters
            },
            sort_keys=True
        )

        cached = redis_client.get(cache_key)

        if cached is not None:
            return json.loads(cached), cache_key

        return None, cache_key

    except RedisError:
        logger.warning("Redis cache unavailable")
        return None, None


def set_cached_products(cache_key: str | None, products: list):
    if cache_key is None:
        return

    try:
        redis_client.set(
            cache_key,
            json.dumps(products),
            ex=CACHE_TTL
        )
    except RedisError:
        logger.warning("Could not save product cache")


def invalidate_product_cache():
    try:
        redis_client.incr(VERSION_KEY)
    except RedisError:
        logger.warning("Could not invalidate product cache")
