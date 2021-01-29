import pytest
import typer
from pytest_mock import MockerFixture

from panda_simple_releases._app._config import APP_NAME
from panda_simple_releases._app._version_handler import version_callback


def test_version_callback_false(capsys: pytest.CaptureFixture[str]) -> None:
    version_callback(version_flag=False, package_name=APP_NAME)
    assert capsys.readouterr().out.strip() == ''


def test_version_callback_true(capsys: pytest.CaptureFixture[str], mocker: MockerFixture) -> None:
    version_patch = mocker.patch('importlib.metadata.version', return_value='1.2.3')
    with pytest.raises(typer.Exit, check=lambda exc: exc.exit_code == 0):
        version_callback(version_flag=True, package_name=APP_NAME)
    version_patch.assert_called_once_with(APP_NAME)
    assert capsys.readouterr().out.strip() == 'panda-simple-releases version 1.2.3'


def test_version_callback_unknown_package(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(typer.Exit, check=lambda exc: exc.exit_code == 0):
        version_callback(version_flag=True, package_name='not-a-real-package')
    assert capsys.readouterr().out.strip() == 'not-a-real-package version unknown'
