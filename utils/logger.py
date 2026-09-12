# https://stackoverflow.com/questions/16929639/ensuring-python-logging-in-multiple-threads-is-thread-safe

import logging
from settings import settings

class Colors:
    """Console Colors"""
    reset = '\x1B[0m'
    bold = '\x1b[1m'
    dim = "\x1b[2m"
    underline = '\x1B[4m'
    blink = '\x1b[5m'
    reverse = "\x1b[7m"  # BACKGROUND
    hidden = "\x1b[8m"

    Black = '\x1B[30m'
    Red = '\x1B[31m'
    Green = '\x1B[32m'
    Yellow = '\x1B[33m'
    Blue = '\x1B[34m'
    Magenta = '\x1B[35m'
    Cyan = '\x1B[36m'
    White = '\x1B[37m'
    Grey = '\x1B[38m'


class CustomFormatter(logging.Formatter):
    MESSAGE_FORMATS = {
        logging.DEBUG: Colors.Blue,
        logging.INFO: Colors.Green,
        logging.WARNING: Colors.Yellow,
        logging.ERROR: Colors.Red,
        logging.CRITICAL: Colors.underline + Colors.bold + Colors.Red,
    }

    def __init__(self, colored=True, *args, **kwargs):
        self.colored = colored
        super().__init__(*args, **kwargs)

    def format(self, record):
        log_format = settings.LOGGING_FORMAT
        if self.colored:
            message_colored = self.MESSAGE_FORMATS[record.levelno] + "{message}" + Colors.reset
            log_format = log_format.replace('{message}', message_colored)

        formatter = logging.Formatter(log_format, style='{', datefmt='%d/%m/%Y %H:%M:%S')
        return formatter.format(record)


# class that used for print information
logger = logging.getLogger()
logger.setLevel(min(settings.LOGGING_LEVEL_DISPLAY, settings.LOGGING_LEVEL_FILESTREAM))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(settings.LOGGING_LEVEL_DISPLAY)
stream_handler.setFormatter(CustomFormatter(colored=True))
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(settings.LOGGING_FILENAME)
file_handler.setLevel(settings.LOGGING_LEVEL_FILESTREAM)
file_handler.setFormatter(CustomFormatter(colored=False))
logger.addHandler(file_handler)

if __name__ == '__main__':
    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.error('error')
    logger.fatal('fatal!!!!')