import logging
import traceback

class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

    def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            exc_info = kwargs.pop('exc_info', None)
            if not exc_info:
                exc_info = (None, None, None)
            else:
                exc_type, exc_value, tb = exc_info
                traceback_info = traceback.extract_tb(tb)
                if traceback_info:
                    filename, lineno, _, _ = traceback_info[-1]
                    msg = f"Error occurred in file {filename}, line {lineno}: {msg}"
            self._log(logging.ERROR, msg, args, **kwargs)


"""Create and configure the logger"""
logger = CustomLogger(__name__)
logger.setLevel(logging.DEBUG)

"""Create a file handler and set its level to DEBUG"""
file_handler = logging.FileHandler('app/files/log_file.log')
file_handler.setLevel(logging.DEBUG)

"""Create a stream handler and set its level to INFO"""
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

"""Create a formatter and add it to the handlers"""
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

"""Add the handlers to the logger"""
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
