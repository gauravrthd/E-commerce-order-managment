
import logging
import time

from fastapi import Request

logger = logging.getLogger("ecommerce")

# define logging middlware fucntion (async) its give execution time
async def logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        duration = time.perf_counter() - start_time

        logger.exception(
            "%s %s failed in %.3f seconds",
            request.method,
            request.url.path,
            duration
        )
        raise

    duration = time.perf_counter() - start_time

    logger.info(
        "%s %s - %s - %.3f seconds",
        request.method,
        request.url.path,
        response.status_code,
        duration
    )

    response.headers["X-Process-Time"] = f"{duration:.3f}"

    return response
