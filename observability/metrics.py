
import os

from prometheus_client import (
    Counter,
    Histogram,
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    generate_latest,
    multiprocess
)

from fastapi import Response


REQUEST_COUNT = Counter(
    "ecommerce_http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"]
)

REQUEST_DURATION = Histogram(
    "ecommerce_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"]
)

REQUEST_ERRORS = Counter(
    "ecommerce_http_errors_total",
    "Total HTTP responses with status >= 500",
    ["method", "route"]
)


def record_request(method, route, status, duration):
    REQUEST_COUNT.labels(
        method=method,
        route=route,
        status=str(status)
    ).inc()

    REQUEST_DURATION.labels(
        method=method,
        route=route
    ).observe(duration)

    if status >= 500:
        REQUEST_ERRORS.labels(
            method=method,
            route=route
        ).inc()


def metrics_endpoint():
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        from prometheus_client import REGISTRY
        registry = REGISTRY

    data = generate_latest(registry)

    return Response(
        content=data,
        media_type=CONTENT_TYPE_LATEST
    )
