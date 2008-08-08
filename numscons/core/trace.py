import logging

from numscons.core.errors import NumsconsError

CRITICAL = logging.CRITICAL

def set_logging(env):
    vlevels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
    try:
        level = env['log_level']
        if not level in vlevels:
            try:
                level = int(level)
            except ValueError:
                raise NumsconsError(
                    "level is %s (type %s), but should be an integer or in %s" \
                    % (level, type(level), vlevels))

    except KeyError:
        level = logging.CRITICAL

    logging.basicConfig(level = level)
    logger = logging.getLogger('numscons')

def warn(*args, **kw):
    logger = logging.getLogger('numscons')
    return logger.warn(*args, **kw)

def info(*args, **kw):
    logger = logging.getLogger('numscons')
    return logger.info(*args, **kw)

def debug(*args, **kw):
    logger = logging.getLogger('numscons')
    return logger.debug(*args, **kw)
