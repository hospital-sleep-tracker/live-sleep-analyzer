__author__ = 'dano'
import logging
import logging.handlers

log = logging.getLogger('sleep-logger')
log.setLevel(logging.DEBUG)

# Create File logger
fh = logging.FileHandler('sleeplogger.log')
fh.setLevel(logging.INFO)

# Create Console Logger
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Set Formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# Add handlers
log.addHandler(ch)
log.addHandler(fh)