import logging
from logging.handlers import RotatingFileHandler
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if not os.path.exists("logs"):
    os.makedirs("logs")

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(f"{os.getcwd()}/app.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

rotating_file_handler = RotatingFileHandler(
    f"{os.getcwd()}/app.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
rotating_file_handler.setLevel(logging.ERROR)
rotating_file_handler.setFormatter(formatter)
logger.addHandler(rotating_file_handler)