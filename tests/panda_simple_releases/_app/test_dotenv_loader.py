from pathlib import Path
from unittest.mock import MagicMock

import pytest
import typer
from pytest_mock import MockerFixture

from panda_simple_releases._app._dotenv_loader import load_dotenv


_PREFIX = 'TEST_PREFIX'


@pytest.fixture(autouse=True)
def find_dotenv_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch('dotenv.find_dotenv')


@pytest.fixture(autouse=True)
def load_dotenv_mock(mocker: MockerFixture) -> MagicMock:
    return mocker.patch('dotenv.load_dotenv')


def test_load_dotenv_not_existing_file(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    find_dotenv_mock: MagicMock,
    load_dotenv_mock: MagicMock,
) -> None:
    file_name = 'not_a_real_file.env'
    monkeypatch.setenv(f'{_PREFIX}_DOTENV_FILE', file_name)
    with pytest.raises(typer.Exit, check=lambda exc: exc.exit_code == 1):
        load_dotenv(_PREFIX)
    assert capsys.readouterr().err.strip() == f'The specified dotenv file does not exist: {file_name}'
    find_dotenv_mock.assert_not_called()
    load_dotenv_mock.assert_not_called()


def test_load_dotenv_specific_file_set(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    find_dotenv_mock: MagicMock,
    load_dotenv_mock: MagicMock,
    tmp_path: Path,
) -> None:
    file_name = 'real_file.env'
    dotenv_file = tmp_path / file_name
    dotenv_file.touch()
    monkeypatch.setenv(f'{_PREFIX}_DOTENV_FILE', str(dotenv_file))
    load_dotenv(_PREFIX)
    find_dotenv_mock.assert_not_called()
    load_dotenv_mock.assert_called_once_with(str(dotenv_file), override=False)
    assert capsys.readouterr().err.strip() == ''


def test_load_dotenv_specific_file_not_set(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    find_dotenv_mock: MagicMock,
    load_dotenv_mock: MagicMock,
) -> None:
    monkeypatch.delenv(f'{_PREFIX}_DOTENV_FILE', raising=False)
    load_dotenv(_PREFIX)
    find_dotenv_mock.assert_called_once_with(usecwd=True)
    load_dotenv_mock.assert_called_once_with(find_dotenv_mock.return_value, override=False)
    assert capsys.readouterr().err.strip() == ''
