import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s - %(name)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
