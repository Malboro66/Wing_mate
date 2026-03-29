import logging


class LogManager:
    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)
