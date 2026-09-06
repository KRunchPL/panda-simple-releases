from pathlib import Path

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from panda_simple_releases._change import Change, ChangeType
from panda_simple_releases._changelog_modifier import (
    _generate_change_string,
    _generate_changelog_entry,
    _insert_into_changelog,
    add_new_version_to_changelog,
)


_TESTED_MODULE = add_new_version_to_changelog.__module__


def test_add_new_version_to_changelog(mocker: MockerFixture):
    generate_mock = mocker.patch(_TESTED_MODULE + '._generate_changelog_entry')
    insert_mock = mocker.patch(_TESTED_MODULE + '._insert_into_changelog')

    changelog_file = Path('some_folder') / 'change.test'
    version = '5.6.3'
    changes = [Change(change_type=ChangeType.SKIP, scope=None, title='This is title', description=[])]

    add_new_version_to_changelog(
        changelog_file=changelog_file,
        version=version,
        changes=changes,
    )

    generate_mock.assert_called_once_with(version, changes)
    insert_mock.assert_called_once_with(changelog_file, generate_mock.return_value)


def test_generate_changelog_entry_empty_list():
    with pytest.raises(ValueError, match='no changes'):
        _generate_changelog_entry(changes=[], version='1.4.2')


@pytest.mark.parametrize(
    ['changes', 'expected_lines'],
    [
        (
            [Change(change_type=ChangeType.SKIP, scope=None, title='This is title', description=[])],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- This is title',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- This is title',
                '',
                '    This is a description',
                '',
                '    This is another description',
            ],
        ),
        (
            [
                Change(change_type=ChangeType.SKIP, scope=None, title='This is title', description=[]),
                Change(change_type=ChangeType.MAJOR, scope=None, title='Another title', description=[]),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- This is title',
                '',
                '- Another title',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
                Change(change_type=ChangeType.MAJOR, scope=None, title='Another title', description=[]),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- This is title',
                '',
                '    This is a description',
                '',
                '    This is another description',
                '',
                '- Another title',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.SKIP,
                    scope=None,
                    title='This is title',
                    description=[],
                ),
                Change(
                    change_type=ChangeType.MAJOR,
                    scope=None,
                    title='Another title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- This is title',
                '',
                '- Another title',
                '',
                '    This is a description',
                '',
                '    This is another description',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'Some description',
                        '',
                        'More description',
                    ],
                ),
                Change(
                    change_type=ChangeType.MAJOR,
                    scope=None,
                    title='Another title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- This is title',
                '',
                '    Some description',
                '',
                '    More description',
                '',
                '- Another title',
                '',
                '    This is a description',
                '',
                '    This is another description',
            ],
        ),
        (
            [Change(change_type=ChangeType.CHORE, scope=None, title='This is title', description=[])],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '### Development',
                '',
                '- This is title',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.CHORE,
                    scope=None,
                    title='This is title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '    This is a description',
                '',
                '    This is another description',
            ],
        ),
        (
            [
                Change(change_type=ChangeType.CHORE, scope=None, title='This is title', description=[]),
                Change(change_type=ChangeType.CHORE_SKIP, scope=None, title='Another title', description=[]),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '- Another title',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.CHORE_SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
                Change(change_type=ChangeType.CHORE, scope=None, title='Another title', description=[]),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '    This is a description',
                '',
                '    This is another description',
                '',
                '- Another title',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.CHORE,
                    scope=None,
                    title='This is title',
                    description=[],
                ),
                Change(
                    change_type=ChangeType.CHORE,
                    scope=None,
                    title='Another title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '- Another title',
                '',
                '    This is a description',
                '',
                '    This is another description',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.CHORE_SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'Some description',
                        '',
                        'More description',
                    ],
                ),
                Change(
                    change_type=ChangeType.CHORE_SKIP,
                    scope=None,
                    title='Another title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '    Some description',
                '',
                '    More description',
                '',
                '- Another title',
                '',
                '    This is a description',
                '',
                '    This is another description',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.CHORE_SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'Some description',
                        '',
                        'More description',
                    ],
                ),
                Change(
                    change_type=ChangeType.MAJOR,
                    scope=None,
                    title='Another title',
                    description=[
                        'This is a description',
                        '',
                        'This is another description',
                    ],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- Another title',
                '',
                '    This is a description',
                '',
                '    This is another description',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '    Some description',
                '',
                '    More description',
            ],
        ),
        (
            [
                Change(
                    change_type=ChangeType.CHORE_SKIP,
                    scope=None,
                    title='This is title',
                    description=[
                        'Some description',
                        '',
                        'More description',
                    ],
                ),
                Change(
                    change_type=ChangeType.MAJOR,
                    scope=None,
                    title='Another title',
                    description=[],
                ),
            ],
            [
                '## [1.4.2] - 2012-01-14',
                '',
                '- Another title',
                '',
                '### Development',
                '',
                '- This is title',
                '',
                '    Some description',
                '',
                '    More description',
            ],
        ),
    ],
)
def test_generate_changelog_entry(changes: list[Change], expected_lines: list[str]):
    with freeze_time('2012-01-14'):
        result = _generate_changelog_entry(changes=changes, version='1.4.2')

    assert result == '\n'.join(expected_lines)


@pytest.mark.parametrize(
    ['change', 'expected'],
    [
        (
            Change(change_type=ChangeType.SKIP, scope=None, title='This is title', description=[]),
            '- This is title',
        ),
        (
            Change(
                change_type=ChangeType.MAJOR,
                scope='some-scope',
                title='Another title',
                description=[
                    '',
                    'First line',
                    '',
                    '    Indentation line    ',
                    '',
                    '- List element',
                    '- Another list element',
                    '',
                ],
            ),
            (
                '- Another title\n'
                '\n'
                '\n'
                '    First line\n'
                '\n'
                '        Indentation line    \n'
                '\n'
                '    - List element\n'
                '    - Another list element\n'
                ''
            ),
        ),
    ],
)
def test_generate_change_string(change: Change, expected: str):
    result = _generate_change_string(change)

    assert result == expected


def test_insert_into_changelog_no_file(tmp_path: Path):
    changelog_file = tmp_path / 'test_file.txt'

    _insert_into_changelog(changelog_file, '\nSome text\nThis is a test entry.\n\n')

    assert (
        changelog_file.read_text(encoding='utf-8')
        == """\
# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


Some text
This is a test entry.


"""
    )


def test_insert_into_changelog_no_previous_entries(tmp_path: Path):
    changelog_file = tmp_path / 'test_file.txt'

    preample = """\


Some text

Here is more text.



"""
    changelog_file.write_text(preample, encoding='utf-8')

    _insert_into_changelog(changelog_file, '\nSome text\nThis is a test entry.\n\n')

    assert (
        changelog_file.read_text(encoding='utf-8')
        == """\


Some text

Here is more text.





Some text
This is a test entry.


"""
    )


def test_insert_into_changelog_previous_entries(tmp_path: Path):
    changelog_file = tmp_path / 'test_file.txt'

    preample = """\


Some text

Here is more text.



"""
    previous_entries = """\


## [ something

sdasdasd

## [ something else

- More text

### Development

- Dev entries

## [additional entries




"""
    changelog_file.write_text(f'{preample}{previous_entries}', encoding='utf-8')

    _insert_into_changelog(changelog_file, '\nSome text\nThis is a test entry.\n\n')

    assert (
        changelog_file.read_text(encoding='utf-8')
        == """\


Some text

Here is more text.


Some text
This is a test entry.



## [ something

sdasdasd

## [ something else

- More text

### Development

- Dev entries

## [additional entries
"""
    )


def test_insert_into_changelog_real_life(tmp_path: Path):
    changelog_file = tmp_path / 'test_file.txt'

    previous = """\
# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-08-27

### Added

- Dynamic rules downloading now supports also groups (e.g., ANN, PT)

## [2.1.0] - 2026-07-25

### Added

- `workdir` is created if it does not exist

## [2.0.0] - 2026-07-25

### Changed

- Dynamic rules downloading instead of hardcoding them in app configuration
- Rewriting for typer

### Removed

- Ability to run just one of the commands
- KRunchPL overrides are no longer included in the default app configuration
"""

    changelog_file.write_text(f'{previous}', encoding='utf-8')

    _insert_into_changelog(
        changelog_file,
        """\
## [2.4.0] - 2027-07-25

- Here is a prod change

### Development

- Here is a dev change""",
    )

    assert (
        changelog_file.read_text(encoding='utf-8')
        == """\
# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2027-07-25

- Here is a prod change

### Development

- Here is a dev change

## [2.2.0] - 2026-08-27

### Added

- Dynamic rules downloading now supports also groups (e.g., ANN, PT)

## [2.1.0] - 2026-07-25

### Added

- `workdir` is created if it does not exist

## [2.0.0] - 2026-07-25

### Changed

- Dynamic rules downloading instead of hardcoding them in app configuration
- Rewriting for typer

### Removed

- Ability to run just one of the commands
- KRunchPL overrides are no longer included in the default app configuration
"""
    )
