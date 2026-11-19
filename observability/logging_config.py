
import logging
import os
import sys

from contextvars import ContextVar
from pythonjsonlogger.json import JsonFormatter


request_id_var = ContextVar(
    "request_id",
    default="-"
)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def configure_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO
    )

    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s "
        "%(message)s %(request_id)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True
    )

    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING
    )
