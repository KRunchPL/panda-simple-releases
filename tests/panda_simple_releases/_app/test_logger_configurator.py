import sys
from pathlib import Path
from typing import Literal, TYPE_CHECKING
from unittest.mock import call, MagicMock

import pytest
from loguru import logger
from pytest_mock import MockerFixture

from panda_simple_releases._app._logger_configurator import (
    _FORMATS,
    _PythonToLoguruRedirectHandler,
    configure_logger,
    LoggerConfiguration,
)


if TYPE_CHECKING:
    from loguru import Message

_MODULE_PATH = configure_logger.__module__


@pytest.fixture
def logger_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(_MODULE_PATH + '.logger')


@pytest.mark.parametrize(
    ['console_level', 'log_format'],
    [
        ('DEBUG', _FORMATS['FULL']),
        ('INFO', _FORMATS['RAW_MSG']),
        ('WARNING', _FORMATS['RAW_MSG']),
    ],
)
@pytest.mark.parametrize(
    ['console_stream', 'sink'],
    [
        ('stdout', sys.stdout),
        ('stderr', sys.stderr),
    ],
)
def test_setup_logging_console_only(
    logger_mock: MagicMock,
    console_level: Literal['DEBUG', 'INFO', 'WARNING'],
    log_format: str,
    console_stream: Literal['stdout', 'stderr'],
    sink: object,
) -> None:
    configure_logger(
        LoggerConfiguration(
            console_level=console_level,
            console_stream=console_stream,
            logs_path=None,
            redirect_python_logging=False,
        ),
    )
    assert logger_mock.mock_calls == [
        call.remove(),
        call.add(
            sink,
            level=console_level,
            format=log_format,
            backtrace=False,
            diagnose=False,
        ),
    ]


def test_setup_logging_with_file_logging(
    logger_mock: MagicMock,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    mkdir_mock = mocker.patch.object(Path, 'mkdir')
    prefix = 'test_'
    config = LoggerConfiguration(
        logs_path=tmp_path,
        file_prefix=prefix,
        console_level='INFO',
    )
    configure_logger(config)
    mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
    assert logger_mock.mock_calls == [
        call.remove(),
        call.add(
            sys.stdout,
            level='INFO',
            format=_FORMATS['RAW_MSG'],
            backtrace=False,
            diagnose=False,
        ),
        call.add(
            tmp_path / 'test_info.log',
            level='INFO',
            format=_FORMATS['NO_SOURCE'],
            backtrace=False,
            diagnose=False,
        ),
        call.add(
            tmp_path / 'test_debug.log',
            level='DEBUG',
            format=_FORMATS['FULL'],
            backtrace=True,
            diagnose=True,
        ),
    ]


@pytest.mark.usefixtures('logger_mock')
def test_redirect_python_logging_true_calls_redirector(mocker: MockerFixture) -> None:
    handler_mock = mocker.patch(_MODULE_PATH + '._PythonToLoguruRedirectHandler')
    config_mock = mocker.patch('logging.basicConfig')

    configure_logger(LoggerConfiguration(redirect_python_logging=True))

    handler_mock.assert_called_once_with()
    config_mock.assert_called_once_with(handlers=[handler_mock.return_value], level=0, force=True)


@pytest.mark.usefixtures('logger_mock')
def test_redirect_python_logging_false_does_not_call_redirector(mocker: MockerFixture) -> None:
    handler_mock = mocker.patch(_MODULE_PATH + '._PythonToLoguruRedirectHandler')
    config_mock = mocker.patch('logging.basicConfig')

    configure_logger(LoggerConfiguration(redirect_python_logging=False))

    handler_mock.assert_not_called()
    config_mock.assert_not_called()


class DummySink:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    def __call__(self, message: Message) -> None:
        self.messages.append(message)


_FORMAT = '<level>{level: <8}</level> | <level>{message}</level>'


@pytest.mark.parametrize(
    ['record_level', 'expected_loguru_level_name', 'expected_loguru_level_no'],
    [
        ('DEBUG', 'DEBUG', 10),
        ('INFO', 'INFO', 20),
        ('WARNING', 'WARNING', 30),
        ('ERROR', 'ERROR', 40),
        ('CRITICAL', 'CRITICAL', 50),
        ('UNKNOWN', 'Level 13', 13),
    ],
)
@pytest.mark.parametrize('record_levelno', [13])
def test_emit(
    record_level: str,
    expected_loguru_level_name: str,
    expected_loguru_level_no: int,
    record_levelno: int,
) -> None:
    handler = _PythonToLoguruRedirectHandler()
    record = MagicMock()
    record.getMessage.return_value = 'Test log message'
    record.args = {
        'key_1': 'value_1',
        'key_2': 'value_2',
    }
    record.levelname = record_level
    record.levelno = record_levelno
    logger.remove()
    logger.add(sink := DummySink(), level=0, format=_FORMAT)

    handler.emit(record)

    assert len(sink.messages) == 1
    assert sink.messages[0].record['message'] == 'Test log message'
    assert sink.messages[0].record['level'].name == expected_loguru_level_name
    assert sink.messages[0].record['level'].no == expected_loguru_level_no
    assert sink.messages[0].record['extra'] == {'args': record.args}


def test_emit_with_curly_bracket_in_message():
    handler = _PythonToLoguruRedirectHandler()
    record = MagicMock()
    message = r'{what}'
    args = {
        'key_1': 'value_1',
        'key_2': 'value_2',
    }
    record.getMessage.return_value = message
    record.levelname = 'INFO'
    record.args = args
    logger.remove()
    logger.add(sink := DummySink(), level=0, format=_FORMAT)

    handler.emit(record)

    assert len(sink.messages) == 1
    assert sink.messages[0].record['message'] == message
    assert sink.messages[0].record['extra'] == {'args': args}
