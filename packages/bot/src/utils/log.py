import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"

def setup_logger():
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
