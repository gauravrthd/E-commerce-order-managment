
import logging
import time

from uuid import uuid4

from observability.logging_config import request_id_var
from observability.metrics import record_request

logger = logging.getLogger("ecommerce.requests")


class ObservabilityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        token = request_id_var.set(request_id)

        method = scope["method"]
        path = scope["path"]
        start_time = time.perf_counter()

        status_code = 500
        error = None

        async def send_with_request_id(message):
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                headers = list(
                    message.get("headers", [])
                )

                headers.append(
                    (
                        b"x-request-id",
                        request_id.encode("ascii")
                    )
                )

                message["headers"] = headers

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id
            )

        except Exception as exc:
            error = exc
            status_code = 500

            logger.exception(
                "Unhandled request exception",
                extra={
                    "method": method,
                    "path": path
                }
            )

            raise

        finally:
            duration = time.perf_counter() - start_time

            route_object = scope.get("route")
            route = getattr(
                route_object,
                "path",
                "unmatched"
            )

            if path != "/metrics":
                record_request(
                    method,
                    route,
                    status_code,
                    duration
                )

                if error is not None or status_code >= 500:
                    log_level = logging.ERROR
                elif status_code >= 400:
                    log_level = logging.WARNING
                else:
                    log_level = logging.INFO

                logger.log(
                    log_level,
                    "HTTP request completed",
                    extra={
                        "method": method,
                        "path": path,
                        "route": route,
                        "status_code": status_code,
                        "duration_ms": round(
                            duration * 1000,
                            2
                        )
                    }
                )

            request_id_var.reset(token)
