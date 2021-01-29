import inspect
import logging
import sys
from pathlib import Path
from typing import Annotated, Literal

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


def configure_logger(config: LoggerConfiguration) -> LoggerConfiguration:
    """
    Configure the logger based on the provided configuration.

    :param config: LoggerConfiguration object containing the desired logger settings.
    :return: The same LoggerConfiguration object for potential further use.
    """
    logger.remove()  # Remove any existing handlers
    logger.add(
        sys.stdout if config.console_stream == 'stdout' else sys.stderr,
        level=config.console_level,
        format=_FORMATS['FULL'] if config.console_level == 'DEBUG' else _FORMATS['RAW_MSG'],
        backtrace=False,
        diagnose=False,
    )
    if config.logs_path:
        config.logs_path.mkdir(parents=True, exist_ok=True)
        logger.add(
            config.logs_path / f'{config.file_prefix}info.log',
            level='INFO',
            format=_FORMATS['NO_SOURCE'],
            backtrace=False,
            diagnose=False,
        )
        logger.add(
            config.logs_path / f'{config.file_prefix}debug.log',
            level='DEBUG',
            format=_FORMATS['FULL'],
            backtrace=True,
            diagnose=True,
        )
    if config.redirect_python_logging:
        logging.basicConfig(
            handlers=[_PythonToLoguruRedirectHandler()],
            level=0,
            force=True,
        )
    return config


class LoggerConfiguration(BaseModel):
    """
    Logger configuration settings.
    """

    model_config = ConfigDict(extra='forbid')

    logs_path: Annotated[
        Path | None,
        Field(description='folder to write log files to'),
    ] = None
    file_prefix: Annotated[
        str,
        Field(description='string to prefix log files names with'),
    ] = ''
    console_level: Annotated[
        Literal['DEBUG', 'INFO', 'WARNING'],
        Field(description='level of the console logs'),
    ] = 'INFO'
    console_stream: Annotated[
        Literal['stdout', 'stderr'],
        Field(description='stream to which console logs are written'),
    ] = 'stdout'
    redirect_python_logging: Annotated[
        bool,
        Field(description='indicates whether to redirect Python logging to loguru'),
    ] = True


_FORMATS = {
    'FULL': (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
        '<level>{level: <8}</level> | '
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
    ),
    'NO_SOURCE': (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
        '<level>{level: <8}</level> | '
        '<level>{message}</level>'
    ),
    'RAW_MSG': '<level>{message}</level>',
}


class _PythonToLoguruRedirectHandler(logging.Handler):
    """
    Handler that redirects Python logging to Loguru.

    Copied from: https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(args=record.args).log(
            level,
            record.getMessage(),
        )
