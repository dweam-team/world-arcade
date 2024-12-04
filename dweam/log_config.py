import logging
import os

import structlog
from structlog.dev import plain_traceback
from structlog.processors import dict_tracebacks


_configured = False


_default_log_level = logging.DEBUG


def _find_log_level_env_var():
    if "LOG_LEVEL" not in os.environ:
        return None

    level_str = os.environ["LOG_LEVEL"]

    if level_str in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        return getattr(logging, level_str)

    try:
        level_int = int(level_str)
    except TypeError:
        return None

    if level_int in [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]:
        return level_int

    return None


def configure_logging(pretty=True, additional_processors=None, level=None):
    if additional_processors is None:
        additional_processors = []

    if level is None:
        level = _find_log_level_env_var()
    if level is None:
        level = _default_log_level

    logging.basicConfig(
        level=level,
    )
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )

    library_log_level = max(level, logging.INFO)

    # silence the boto3 logs a bit
    logging.getLogger("openai").setLevel(library_log_level)
    # logging.getLogger("httpx").setLevel(logging.INFO)
    # logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(library_log_level)
    logging.getLogger("aioboto3").setLevel(library_log_level)
    logging.getLogger("botocore").setLevel(library_log_level)
    logging.getLogger("aiobotocore").setLevel(library_log_level)
    logging.getLogger("aiortc").setLevel(library_log_level)
    logging.getLogger("jax").setLevel(library_log_level)

    processors = additional_processors + [
        structlog.stdlib.add_log_level,  # add log level
    ]

    if pretty:
        processors += [
            structlog.dev.set_exc_info,  # add exception info
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        ]
        processors += [
            structlog.dev.ConsoleRenderer(
                exception_formatter=plain_traceback,
                colors=not bool(os.environ.get("SUPPRESS_LOG_COLORS")),
            ),
        ]
    else:
        processors += [
            dict_tracebacks,  # add exception info
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        cache_logger_on_first_use=True,
    )

    global _configured
    _configured = True


def get_logger(*args, **kwargs) -> structlog.stdlib.BoundLogger:
    # Configure logging on first logger use, if not configured yet
    if not _configured:
        configure_logging()

    log = structlog.get_logger(*args, **kwargs)
    return log
