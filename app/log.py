import logging

from datetime import date


src = 'static/logs/'
logging.basicConfig(level=logging.INFO, filename=f"{src}py_log.log", filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


def log_expect(err):
    logging.exception(err)


def log_info(info):
    logging.info(info)
