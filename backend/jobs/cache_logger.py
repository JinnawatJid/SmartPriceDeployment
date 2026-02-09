# cache_logger.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = "logs/customer_cache_refresh.log"
LOG_LEVEL = "INFO"
LOG_BACKUP_COUNT = 30

def setup_cache_logger():
    logger = logging.getLogger('customer_cache')
    logger.setLevel(getattr(logging, LOG_LEVEL))
    logger.handlers.clear()
    
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

cache_logger = setup_cache_logger()
