import logging
import os
import sys

from datetime import date

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(PROJECT_ROOT, '..', 'static', 'logs')
LOG_FILE_PATH = os.path.join(LOGS_DIR, 'py_log.log')

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE_PATH,
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def log_expect(err):
    logging.exception(err)


def log_info(info):
    logging.info(info)
