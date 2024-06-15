import logging

DEFAULT_FORMAT = "[%(asctime)s %(levelname)s %(name)s %(threadName)s %(filename)s:%(lineno)s] %(message)s"


def build_log_config(log_level: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"()": logging.Formatter, "format": DEFAULT_FORMAT}},
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "src": {"level": log_level, "handlers": ["default"], "propagate": False},
            "recommendations": {
                "level": log_level,
                "handlers": ["default"],
                "propagate": False,
            },
            "chat": {"level": log_level, "handlers": ["default"], "propagate": False},
            "aiogram": {
                "level": log_level,
                "handlers": ["default"],
                "propagate": False,
            },
        },
    }
