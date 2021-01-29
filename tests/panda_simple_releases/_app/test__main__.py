from unittest.mock import call, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from panda_simple_releases._app.__main__ import app, main
from panda_simple_releases._app._config import APP_NAME, ENV_VAR_PREFIX
from panda_simple_releases._app._version_handler import version_callback


_TESTED_MODULE = main.__module__


@app.command('testing_noop')
def _noop(): ...


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_debug_passed(cli_runner: CliRunner, mocker: MockerFixture) -> None:
    logger_configuration_mock = mocker.patch(_TESTED_MODULE + '.LoggerConfiguration')
    configure_logger_mock = mocker.patch(_TESTED_MODULE + '.configure_logger')

    result = cli_runner.invoke(app, ['--debug', 'testing_noop'])

    logger_configuration_mock.assert_called_once_with(console_level='DEBUG')
    configure_logger_mock.assert_called_once_with(logger_configuration_mock.return_value)
    assert result.exit_code == 0
    assert result.stdout.strip() == ''
    assert result.output.strip() == ''
    assert result.stderr.strip() == ''


def test_debug_not_passed(cli_runner: CliRunner, mocker: MockerFixture) -> None:
    logger_configuration_mock = mocker.patch(_TESTED_MODULE + '.LoggerConfiguration')
    configure_logger_mock = mocker.patch(_TESTED_MODULE + '.configure_logger')

    result = cli_runner.invoke(app, ['testing_noop'])

    logger_configuration_mock.assert_called_once_with(console_level='INFO')
    configure_logger_mock.assert_called_once_with(logger_configuration_mock.return_value)
    assert result.exit_code == 0
    assert result.stdout.strip() == ''
    assert result.output.strip() == ''
    assert result.stderr.strip() == ''


def test_version_passed(cli_runner: CliRunner, mocker: MockerFixture) -> None:
    version_callback_mock = mocker.patch(_TESTED_MODULE + '.version_callback', side_effect=version_callback)

    result = cli_runner.invoke(app, ['--version', 'testing_noop'])

    version_callback_mock.assert_called_once_with(version_flag=True, package_name=APP_NAME)
    assert result.exit_code == 0
    assert f'{APP_NAME} version' in result.output
    assert result.stderr.strip() == ''


def test_version_not_passed(cli_runner: CliRunner, mocker: MockerFixture) -> None:
    version_callback_mock = mocker.patch(_TESTED_MODULE + '.version_callback', side_effect=version_callback)

    result = cli_runner.invoke(app, ['testing_noop'])

    version_callback_mock.assert_called_once_with(version_flag=False, package_name=APP_NAME)
    assert result.exit_code == 0
    assert f'{APP_NAME} version' not in result.output
    assert result.stderr.strip() == ''


def test_execute(cli_runner: CliRunner, mocker: MockerFixture) -> None:
    run_mock = mocker.patch(_TESTED_MODULE + '.run')

    result = cli_runner.invoke(app, ['execute'])

    run_mock.assert_called_once_with()
    assert result.exit_code == 0
    assert result.stdout.strip() == ''
    assert result.output.strip() == ''
    assert result.stderr.strip() == ''


def test_main_flow(mocker: MockerFixture):
    mock = MagicMock()
    for function_name in ('load_dotenv', 'app'):
        mock.attach_mock(
            mocker.patch(_TESTED_MODULE + f'.{function_name}'),
            function_name,
        )

    main()

    assert mock.mock_calls == [
        call.load_dotenv(ENV_VAR_PREFIX),
        call.app(),
    ]
