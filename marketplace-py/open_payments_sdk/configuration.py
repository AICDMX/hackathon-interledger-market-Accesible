import logging


class Configuration:
    def __init__(self):
        self.logging_formatter = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.user_agent = "open-payments-sdk/python"

    def get_log_handler(self) -> logging.Handler:
        """
        Return a logger handler.
        """
        formatter = logging.Formatter(self.logging_formatter)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        return handler
