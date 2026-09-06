import logging
from pathlib import Path
from typing import Any
from unittest.mock import call, MagicMock

import pytest
from pytest_mock import MockerFixture

from panda_simple_releases._change_files_validation import _parse_change_file, validate_change_files
from panda_simple_releases._change_parser import ChangeParserError


_TESTED_MODULE = validate_change_files.__module__

_INSTRUCTIONS_LOGS = [
    (
        logging.INFO,
        (
            'Required format:\n'
            '---\n'
            'Line 1: <change_type>: <message> or <change_type>(<scope>): '
            '<message>\n'
            'Line 2: (blank line)\n'
            'Line 3+: (optional) <description>\n'
            '---\n'
        ),
    ),
    (
        logging.INFO,
        (
            'Valid change types: breaking, major, feat, feature, minor, fix, '
            'bugfix, hotfix, patch, perf, performance, chore, chore-skip, skip\n'
        ),
    ),
    (
        logging.INFO,
        (
            'Example change:\n'
            '---\n'
            'feat: Add new feature\n'
            '\n'
            'This feature does something really cool.\n'
            'It has multiple lines in the description.\n'
            '---\n'
        ),
    ),
]


@pytest.mark.parametrize(
    ['changes', 'expected_changes', 'expected_errors', 'expected_logs'],
    [
        (
            {},
            {},
            {},
            [
                (logging.INFO, '✅ All 0 change file(s) are valid.'),
            ],
        ),
        (
            {
                'file_1': 'change_1',
                'file_2': 'change_2',
            },
            {
                'file_1': 'change_1',
                'file_2': 'change_2',
            },
            {},
            [
                (logging.INFO, '✅ All 2 change file(s) are valid.'),
            ],
        ),
        (
            {
                'file_1': ChangeParserError(change_id='', message='msg_1'),
                'file_2': ChangeParserError(change_id='', message='msg_2'),
            },
            {},
            {
                'file_1': 'msg_1',
                'file_2': 'msg_2',
            },
            [
                (logging.ERROR, '❌ 2 out of 2 change file(s) are invalid. Errors:'),
                (logging.ERROR, '  - "file_1": msg_1'),
                (logging.ERROR, '  - "file_2": msg_2'),
                *_INSTRUCTIONS_LOGS,
            ],
        ),
        (
            {
                'file_1': 'change_1',
                'file_2': ChangeParserError(change_id='', message='msg_2'),
                'file_3': 'change_3',
                'file_4': 'change_4',
                'file_5': ChangeParserError(change_id='', message='msg_5'),
                'file_6': ChangeParserError(change_id='', message='msg_6'),
                'file_7': 'change_7',
            },
            {
                'file_1': 'change_1',
                'file_3': 'change_3',
                'file_4': 'change_4',
                'file_7': 'change_7',
            },
            {
                'file_2': 'msg_2',
                'file_5': 'msg_5',
                'file_6': 'msg_6',
            },
            [
                (
                    logging.WARNING,
                    '⚠️ Only 4 out of 7 change file(s) are valid: "file_1", "file_3", "file_4", "file_7".',
                ),
                (logging.ERROR, '❌ 3 out of 7 change file(s) are invalid. Errors:'),
                (logging.ERROR, '  - "file_2": msg_2'),
                (logging.ERROR, '  - "file_5": msg_5'),
                (logging.ERROR, '  - "file_6": msg_6'),
                *_INSTRUCTIONS_LOGS,
            ],
        ),
    ],
)
def test_validate_change_files(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    changes: dict[str, Any],
    expected_changes: dict[str, Any],
    expected_errors: dict[str, Any],
    expected_logs: list[tuple[int, str]],
):
    parse_mock = mocker.patch(_TESTED_MODULE + '._parse_change_file', side_effect=list(changes.values()))

    change_files = [Path(file) for file in changes]
    with caplog.at_level(logging.DEBUG):
        valid, errors = validate_change_files(change_files)

    assert parse_mock.mock_calls == [call(file) for file in change_files]
    assert valid == expected_changes
    assert errors == expected_errors
    assert caplog.record_tuples == [
        ('panda_simple_releases._change_files_validation', level, msg) for level, msg in expected_logs
    ]


def test_parse_change_file(mocker: MockerFixture):
    file_path = MagicMock()
    parse_string_mock = mocker.patch(_TESTED_MODULE + '.parse_change_from_string')

    result = _parse_change_file(file_path)

    assert result is parse_string_mock.return_value
    file_path.read_text.assert_called_once_with(encoding='utf-8')
    parse_string_mock.assert_called_once_with(file_path.name, file_path.read_text.return_value)
