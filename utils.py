import argparse
import logging

from settings import DEBUG_MODE


def create_logger():
    logger = logging.getLogger(__name__)
    if DEBUG_MODE:
        logging.basicConfig(level=logging.DEBUG)
    return logger


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path')
    parser.add_argument('--port')
    return parser
