from pathlib import Path
from typing import Any
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


@pytest.mark.parametrize(['debug', 'expected_console_level'], [(True, 'DEBUG'), (False, 'INFO')])
def test_debug_flag(
    cli_runner: CliRunner,
    mocker: MockerFixture,
    debug: bool,
    expected_console_level: str,
) -> None:
    logger_configuration_mock = mocker.patch(_TESTED_MODULE + '.LoggerConfiguration')
    configure_logger_mock = mocker.patch(_TESTED_MODULE + '.configure_logger')

    if debug:
        result = cli_runner.invoke(app, ['--debug', 'testing_noop'])
    else:
        result = cli_runner.invoke(app, ['testing_noop'])

    logger_configuration_mock.assert_called_once_with(console_level=expected_console_level)
    configure_logger_mock.assert_called_once_with(logger_configuration_mock.return_value)
    assert result.exit_code == 0
    assert result.stdout.strip() == ''
    assert result.output.strip() == ''
    assert result.stderr.strip() == ''


@pytest.mark.parametrize('version', [True, False])
def test_version_flag(cli_runner: CliRunner, mocker: MockerFixture, version: bool) -> None:
    version_callback_mock = mocker.patch(_TESTED_MODULE + '.version_callback', side_effect=version_callback)

    if version:
        result = cli_runner.invoke(app, ['--version', 'testing_noop'])
    else:
        result = cli_runner.invoke(app, ['testing_noop'])

    version_callback_mock.assert_called_once_with(version_flag=version, package_name=APP_NAME)
    assert result.exit_code == 0
    assert (f'{APP_NAME} version' in result.output) == version
    assert result.stderr.strip() == ''


@pytest.mark.parametrize('changes_folder', [None, 'custom_changes'])
@pytest.mark.parametrize('branch', [None, 'some-branch'])
def test_check_flow(
    cli_runner: CliRunner,
    mocker: MockerFixture,
    changes_folder: str | None,
    branch: str | None,
) -> None:
    discover_change_files_mock = mocker.patch(
        _TESTED_MODULE + '.discover_change_files',
        return_value=[1],
    )
    validate_change_files_mock = mocker.patch(
        _TESTED_MODULE + '.validate_change_files',
        return_value=([], []),
    )

    args = ['check']
    if changes_folder is not None:
        args.extend(['--changes-folder', changes_folder])
        expected_changes_folder = Path(changes_folder)
    else:
        expected_changes_folder = Path('.changes')
    if branch is not None:
        args.extend(['--compare-to-branch', branch])

    result = cli_runner.invoke(app, args)

    discover_change_files_mock.assert_called_once_with(expected_changes_folder, branch)
    validate_change_files_mock.assert_called_once_with(discover_change_files_mock.return_value)
    assert result.exit_code == 0
    assert result.stdout.strip() == ''
    assert result.output.strip() == ''
    assert result.stderr.strip() == ''


@pytest.mark.parametrize(
    ['discovered', 'validated', 'expected_exit_code', 'is_validate_called'],
    [
        ([], ([], []), 1, False),
        ([1], ([], []), 0, True),
        ([1], ([1], [1]), 1, True),
    ],
)
def test_check_logic(
    cli_runner: CliRunner,
    mocker: MockerFixture,
    discovered: list[Any],
    validated: tuple[list[Any], list[Any]],
    expected_exit_code: int,
    is_validate_called: bool,
) -> None:
    discover_change_files_mock = mocker.patch(
        _TESTED_MODULE + '.discover_change_files',
        return_value=discovered,
    )
    validate_change_files_mock = mocker.patch(
        _TESTED_MODULE + '.validate_change_files',
        return_value=validated,
    )

    result = cli_runner.invoke(app, ['check'])

    discover_change_files_mock.assert_called_once()
    if is_validate_called:
        validate_change_files_mock.assert_called_once()
    else:
        validate_change_files_mock.assert_not_called()
    assert result.exit_code == expected_exit_code
    assert result.stdout.strip() == ''
    assert result.output.strip() == ''
    assert result.stderr.strip() == ''


def test_release_flow(cli_runner: CliRunner, mocker: MockerFixture):
    mock = MagicMock()
    for function_name in (
        'discover_change_files',
        'validate_change_files',
        'get_highest_version_bump',
        'bump_version',
        'remove_files',
        'add_new_version_to_changelog',
    ):
        mock.attach_mock(
            mocker.patch(_TESTED_MODULE + f'.{function_name}'),
            function_name,
        )
    mock.validate_change_files.return_value.__iter__.return_value = iter((valid := MagicMock(), []))
    mock.bump_version.return_value.__iter__.return_value = iter((
        old_version := MagicMock(),
        new_version := MagicMock(),
    ))
    mock.reset_mock()

    result = cli_runner.invoke(app, ['release'])

    assert mock.mock_calls == [
        call.discover_change_files(Path('.changes'), None),
        call.discover_change_files().__bool__(),
        call.validate_change_files(mock.discover_change_files.return_value),
        call.validate_change_files().__iter__(),
        call.get_highest_version_bump(valid.values.return_value),
        ('get_highest_version_bump().bump_name.__str__', (), {}),
        call.bump_version(bump_spec=mock.get_highest_version_bump.return_value.bump_name),
        call.bump_version().__iter__(),
        call.remove_files(mock.discover_change_files.return_value),
        call.add_new_version_to_changelog(
            changelog_file=Path('CHANGELOG.md'),
            version=new_version,
            changes=list(valid.values.return_value),
        ),
    ]
    assert result.exit_code == 0
    assert (
        result.output.strip()
        == result.stdout.strip()
        == (
            f'Established bump type is: {mock.get_highest_version_bump.return_value.bump_name}\n'
            f'Updated version from {old_version} to {new_version}\n'
            f'✅ Release completed successfully.'
        )
    )

    assert result.stderr.strip() == ''


@pytest.mark.parametrize(
    [
        'discovered',
        'validated',
        'expected_exit_code',
        'is_validate_called',
        'is_update_logic_called',
        'expected_output',
    ],
    [
        (
            [],
            ([], []),
            1,
            False,
            False,
            '❌ Release aborted due to no change files.',
        ),
        (
            [1],
            ({}, []),
            0,
            True,
            True,
            (
                'Established bump type is: {bump_name}\n'
                'Updated version from {old_version} to {new_version}\n'
                '✅ Release completed successfully.'
            ),
        ),
        (
            [1],
            ({}, [1]),
            1,
            True,
            False,
            '❌ Release aborted due to invalid change files.',
        ),
    ],
)
def test_release_logic(
    cli_runner: CliRunner,
    mocker: MockerFixture,
    discovered: list[Any],
    validated: tuple[list[Any], list[Any]],
    expected_exit_code: int,
    is_validate_called: bool,
    is_update_logic_called: bool,
    expected_output: str,
):
    mock = MagicMock()
    for function_name in (
        'discover_change_files',
        'validate_change_files',
        'get_highest_version_bump',
        'bump_version',
        'remove_files',
        'add_new_version_to_changelog',
    ):
        mock.attach_mock(
            mocker.patch(_TESTED_MODULE + f'.{function_name}'),
            function_name,
        )
    mock.discover_change_files.return_value = discovered
    mock.validate_change_files.return_value = validated
    mock.bump_version.return_value = (MagicMock(), MagicMock())
    mock.reset_mock()

    result = cli_runner.invoke(app, ['release'])

    mock.discover_change_files.assert_called_once()
    if is_validate_called:
        mock.validate_change_files.assert_called_once()
    else:
        mock.validate_change_files.assert_not_called()
    if is_update_logic_called:
        mock.get_highest_version_bump.assert_called_once()
        mock.bump_version.assert_called_once()
        mock.remove_files.assert_called_once()
        mock.add_new_version_to_changelog.assert_called_once()
    else:
        mock.get_highest_version_bump.assert_not_called()
        mock.bump_version.assert_not_called()
        mock.remove_files.assert_not_called()
        mock.add_new_version_to_changelog.assert_not_called()
    assert result.exit_code == expected_exit_code
    assert (
        result.output.strip()
        == result.stdout.strip()
        == expected_output.format(
            bump_name=mock.get_highest_version_bump.return_value.bump_name,
            old_version=mock.bump_version.return_value[0],
            new_version=mock.bump_version.return_value[1],
        )
    )
    assert result.stderr.strip() == ''


@pytest.mark.parametrize(
    'found_version',
    [
        '0.1.0',
        '0.2.0',
        '1.0.0',
    ],
)
def test_show_version_logic(
    cli_runner: CliRunner,
    mocker: MockerFixture,
    found_version: str,
) -> None:
    bump_version_mock = mocker.patch(
        _TESTED_MODULE + '.bump_version',
        return_value=[found_version, MagicMock()],
    )

    result = cli_runner.invoke(app, ['show-version'])

    bump_version_mock.assert_called_once()
    assert result.exit_code == 0
    assert result.stdout.strip() == result.output.strip() == found_version
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
