# logger_config.py

import logging

# Configure the logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Create a logger
logger = logging.getLogger(__name__)
