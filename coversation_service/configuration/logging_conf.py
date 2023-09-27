import sys

from opentelemetry.instrumentation.logging import LoggingInstrumentor
from pydantic import BaseSettings, Field

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            'format': '%(asctime)s'
                      '%(levelname)s'
                      '%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'

        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stderr,
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": [
            "console"
        ],
        "propagate": True
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}
LoggingInstrumentor().instrument(set_logging_format=True)


class OtlpConfig(BaseSettings):
    OTLP_ENDPOINT: str = Field(env="OTLP_ENDPOINT", default="")


otlp_config = OtlpConfig()
