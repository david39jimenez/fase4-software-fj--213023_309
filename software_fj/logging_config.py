from __future__ import annotations

import logging
import os
import traceback
from typing import Optional

_LOGGER: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("software_fj")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Evita duplicar handlers si el módulo se recarga.
    if not logger.handlers:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "software_fj.log")

        handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _LOGGER = logger
    return logger


def log_event(message: str) -> None:
    get_logger().info(message)


def log_error(message: str, exc: BaseException) -> None:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    get_logger().error("%s | %s\n%s", message, str(exc), tb)

