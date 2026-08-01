import logging
import os

from logging.handlers import RotatingFileHandler


os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("sales_app")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

file_handler = RotatingFileHandler(
    "logs/application.log",
    maxBytes=1_000_000,
    backupCount=3
)

file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)