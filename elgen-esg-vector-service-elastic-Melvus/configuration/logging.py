import sys

from loguru import logger

# Configure the logger
logger.remove()  # Remove the default configuration
logger.add(sink="logs.log", level="DEBUG", rotation="10 MB", backtrace=True, diagnose=True, catch=True)  # Add a file sink
logger.add(sink=sys.stdout, level="INFO")  # Add a console sink