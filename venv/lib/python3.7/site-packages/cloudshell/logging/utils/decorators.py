import logging
from functools import wraps


def command_logging(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        func_name = func.__name__

        # extracting logger
        logger = None
        if args:
            logger = getattr(args[0], "logger", None) or getattr(
                args[0], "_logger", None
            )
            if not logger:
                for var in args + tuple(kwargs.values()):
                    if isinstance(var, logging.Logger):
                        logger = var
                        break
        if not logger:
            raise Exception("Logger instance is not defined.")

        logger.debug('Start command "{}"'.format(func_name))
        finishing_msg = 'Command "{}" finished {}'
        try:

            result = func(*args, **kwargs)
        except Exception:
            logger.debug(finishing_msg.format(func_name, "unsuccessfully"))
            raise
        else:
            logger.debug(finishing_msg.format(func_name, "successfully"))

        return result

    return wrapped
