import logging
import sys
from app.core.config import settings

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# single shared logger
logger = setup_logger("postsfusion")