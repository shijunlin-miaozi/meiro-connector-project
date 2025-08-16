import logging
from common.config import settings

_LEVEL = logging._nameToLevel.get((settings.LOG_LEVEL or "INFO").upper(), logging.INFO)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(_LEVEL)
        h = logging.StreamHandler()
        f = logging.Formatter(fmt="ts=%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
                              datefmt="%Y-%m-%dT%H:%M:%S")
        h.setFormatter(f)
        logger.addHandler(h)
        logger.propagate = False
    return logger
