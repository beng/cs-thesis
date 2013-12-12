import os
import logging
from logging.handlers import RotatingFileHandler
from functools import partial

from ..settings.config import GA_LOGS

FORMAT = '\n%(asctime)s  %(levelname)s - %(message)s\n'
NAME = "output-{}.log".format(__name__)
PATH = os.path.join(GA_LOGS, NAME)


def create_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler_map = {
        'RotatingFileHandler': partial(RotatingFileHandler, PATH, **{
            'maxBytes': 100000,
            'backupCount': 5
        }),
        'StreamHandler': logging.StreamHandler
    }
    for handler in ['StreamHandler', 'RotatingFileHandler']:
        _handler = handler_map[handler]()
        _handler.setFormatter(logging.Formatter(FORMAT))
        _handler.setLevel(logging.DEBUG)
        logger.addHandler(_handler)
    return logger


logger = create_logger()
