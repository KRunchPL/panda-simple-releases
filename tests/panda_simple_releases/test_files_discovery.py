import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import call, MagicMock

import pytest
from munch import Munch
from pytest_mock import MockerFixture

from panda_simple_releases._files_discovery import (
    _get_change_files_from_folder,
    _get_change_files_from_git,
    discover_change_files,
)
from panda_simple_releases._git import GitError


_TESTED_MODULE = discover_change_files.__module__


class _DummyPath(Path):
    ABSOLUTE_PATH = Path('dummy_absolute_path')

    def __init__(
        self,
        *,
        exists: bool = True,
        is_dir: bool = True,
        is_file: bool = False,
        files: list[_DummyPath] | None = None,
        name: str = 'i_am_file',
    ) -> None:
        self._exists = exists
        self._is_dir = is_dir
        self._is_file = is_file
        self._files = files if files is not None else []
        self._name = name

    def exists(self, *, follow_symlinks=True) -> bool:
        _ = follow_symlinks
        return self._exists

    def is_dir(self, *, follow_symlinks=True) -> bool:
        _ = follow_symlinks
        return self._is_dir

    def is_file(self, *, follow_symlinks=True) -> bool:
        _ = follow_symlinks
        return self._is_file

    def absolute(self) -> Path:  # type: ignore [override]
        return self.ABSOLUTE_PATH

    def iterdir(self) -> Generator[_DummyPath]:
        yield from self._files

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f'_DummyPath(name={self._name})'


@pytest.mark.parametrize('branch', [None, 'not-important'])
def test_discover_change_files_folder_not_existing(caplog: pytest.LogCaptureFixture, branch: str | None):
    changes_folder = _DummyPath(exists=False)
    with caplog.at_level(logging.DEBUG):
        result = list(discover_change_files(changes_folder, branch))
    assert result == []
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.WARNING,
            f'Path "{_DummyPath.ABSOLUTE_PATH}" does not exist',
        ),
        (
            'panda_simple_releases._files_discovery',
            logging.ERROR,
            '❌ No change files found.',
        ),
    ]


@pytest.mark.parametrize('branch', [None, 'not-important'])
def test_discover_change_files_folder_not_dir(caplog: pytest.LogCaptureFixture, branch: str | None):
    changes_folder = _DummyPath(is_dir=False)
    with caplog.at_level(logging.DEBUG):
        result = list(discover_change_files(changes_folder, branch))
    assert result == []
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.ERROR,
            f'Path "{_DummyPath.ABSOLUTE_PATH}" is not a directory',
        ),
        (
            'panda_simple_releases._files_discovery',
            logging.ERROR,
            '❌ No change files found.',
        ),
    ]


_TEST_CHANGES_FOLDER = _DummyPath()


@pytest.mark.parametrize(
    ['branch', 'expected_calls'],
    [
        (
            None,
            [call._get_change_files_from_folder(_TEST_CHANGES_FOLDER)],
        ),
        (
            'not-important',
            [call._get_change_files_from_git(_TEST_CHANGES_FOLDER, 'not-important')],
        ),
    ],
)
def test_discover_change_files_empty_list(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    branch: str | None,
    expected_calls: list[Any],
):
    change_files: list[Any] = []
    mock = MagicMock()
    for function_name in ('_get_change_files_from_folder', '_get_change_files_from_git'):
        mock.attach_mock(
            mocker.patch(_TESTED_MODULE + f'.{function_name}', return_value=change_files),
            function_name,
        )

    with caplog.at_level(logging.DEBUG):
        result = discover_change_files(_TEST_CHANGES_FOLDER, branch)

    assert mock.mock_calls == expected_calls
    assert result == change_files
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.ERROR,
            '❌ No change files found.',
        ),
    ]


@pytest.mark.parametrize(
    ['branch', 'expected_calls'],
    [
        (
            None,
            [call._get_change_files_from_folder(_TEST_CHANGES_FOLDER)],
        ),
        (
            'not-important',
            [call._get_change_files_from_git(_TEST_CHANGES_FOLDER, 'not-important')],
        ),
    ],
)
def test_discover_change_files_non_empty_list(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    branch: str | None,
    expected_calls: list[Any],
):
    change_files: list[Any] = [
        Munch(name='first'),
        Munch(name='second'),
    ]
    mock = MagicMock()
    for function_name in ('_get_change_files_from_folder', '_get_change_files_from_git'):
        mock.attach_mock(
            mocker.patch(_TESTED_MODULE + f'.{function_name}', return_value=change_files),
            function_name,
        )

    with caplog.at_level(logging.DEBUG):
        result = discover_change_files(_TEST_CHANGES_FOLDER, branch)

    assert mock.mock_calls == expected_calls
    assert result == change_files
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.INFO,
            'Found 2 change file(s): "first", "second".',
        ),
    ]


def test_get_change_files_from_git_empty_result(caplog: pytest.LogCaptureFixture, mocker: MockerFixture):
    changes_folder = Path()
    branch = 'some-branch'
    git_mock = mocker.patch(_TESTED_MODULE + '.get_new_files_since_branched_out', return_value=[])

    with caplog.at_level(logging.DEBUG):
        result = list(_get_change_files_from_git(changes_folder, branch))

    git_mock.assert_called_once_with(branch)
    assert result == []
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.INFO,
            (
                f'Looking for change files in "{changes_folder.absolute()}" '
                f'that were added since branching out from "{branch}"...'
            ),
        ),
    ]


def test_get_change_files_from_git_happy_path(caplog: pytest.LogCaptureFixture, mocker: MockerFixture):
    changes_folder = Path('test-changes')
    branch = 'some-branch'

    change_files = [
        changes_folder / 'file',
        changes_folder / 'another-file',
    ]
    git_result = [
        Path('not-in-folder'),
        change_files[0],
        changes_folder / '.file-with-dot',
        Path('.not-in-folder-with-dot'),
        change_files[1],
    ]

    git_mock = mocker.patch(_TESTED_MODULE + '.get_new_files_since_branched_out', return_value=git_result)

    with caplog.at_level(logging.DEBUG):
        result = list(_get_change_files_from_git(changes_folder, branch))

    git_mock.assert_called_once_with(branch)
    assert result == change_files
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.INFO,
            (
                f'Looking for change files in "{changes_folder.absolute()}" '
                f'that were added since branching out from "{branch}"...'
            ),
        ),
        (
            'panda_simple_releases._files_discovery',
            logging.DEBUG,
            'Ignoring hidden file: ".file-with-dot"',
        ),
    ]


def test_get_change_files_from_git_with_git_error(caplog: pytest.LogCaptureFixture, mocker: MockerFixture):
    changes_folder = Path()
    branch = 'some-branch'
    error_message = 'some-message'
    git_mock = mocker.patch(
        _TESTED_MODULE + '.get_new_files_since_branched_out',
        side_effect=GitError(error_message),
    )

    with caplog.at_level(logging.DEBUG):
        result = list(_get_change_files_from_git(changes_folder, branch))

    git_mock.assert_called_once_with(branch)
    assert result == []
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.INFO,
            (
                f'Looking for change files in "{changes_folder.absolute()}" '
                f'that were added since branching out from "{branch}"...'
            ),
        ),
        (
            'panda_simple_releases._files_discovery',
            logging.ERROR,
            f'❌ Could not fetch change files from git. Error: {error_message}',
        ),
    ]


def test_get_change_files_from_folder_folder_is_empty(caplog: pytest.LogCaptureFixture):
    changes_folder = _DummyPath(files=[])

    with caplog.at_level(logging.DEBUG):
        result = list(_get_change_files_from_folder(changes_folder))

    assert result == []
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.INFO,
            f'Looking for change files in "{changes_folder.absolute()}"...',
        ),
    ]


def test_get_change_files_from_folder_happy_path(caplog: pytest.LogCaptureFixture):
    change_files = [
        _DummyPath(is_file=True, name='file'),
        _DummyPath(is_file=True, name='another-file'),
    ]
    changes_folder = _DummyPath(
        files=[
            _DummyPath(is_file=False, name='not-file'),
            change_files[0],
            _DummyPath(is_file=True, name='.file-with-dot'),
            _DummyPath(is_file=False, name='.not-file-with-dot'),
            change_files[1],
        ],
    )

    with caplog.at_level(logging.DEBUG):
        result = list(_get_change_files_from_folder(changes_folder))

    assert result == change_files
    assert caplog.record_tuples == [
        (
            'panda_simple_releases._files_discovery',
            logging.INFO,
            f'Looking for change files in "{changes_folder.absolute()}"...',
        ),
        (
            'panda_simple_releases._files_discovery',
            logging.DEBUG,
            'Ignoring hidden file: ".file-with-dot"',
        ),
    ]
