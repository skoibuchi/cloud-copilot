
import os
import logging
from logging.handlers import RotatingFileHandler
from app.core.config import settings


class Logger:
    def __init__(self, log_name="app", log_file="app.log", log_level=logging.INFO, max_bytes=5 * 1024 * 1024, backup_count=7):
        log_dir = settings.LOG_DIR
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(log_dir, log_file)

        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
            formatter = logging.Formatter('[%(levelname)s] [%(asctime)s] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
