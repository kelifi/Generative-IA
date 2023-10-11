import logging


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)