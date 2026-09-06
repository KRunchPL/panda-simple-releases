from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from panda_simple_releases._change import get_highest_version_bump
from panda_simple_releases._change_files_validation import validate_change_files
from panda_simple_releases._changelog_modifier import (
    add_new_version_to_changelog,
)
from panda_simple_releases._file_remover import remove_files
from panda_simple_releases._files_discovery import discover_change_files
from panda_simple_releases._version_bumper import bump_version

from ._config import APP_NAME, ENV_VAR_PREFIX
from ._dotenv_loader import load_dotenv
from ._logger_configurator import configure_logger, LoggerConfiguration
from ._version_handler import version_callback


app = typer.Typer(
    name=APP_NAME,
    help='A simple tool for managing releases and changelogs of projects.',
    add_completion=False,
)


@app.callback()
def _(
    *,
    _: Annotated[
        bool,
        typer.Option(
            '--version',
            help='Show the version and exit.',
            is_eager=True,
            callback=lambda value: version_callback(package_name=APP_NAME, version_flag=value),
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            '--debug',
            help='Show debug logs in the console.',
            envvar=f'{ENV_VAR_PREFIX}_DEBUG',
        ),
    ] = False,
) -> None:
    logger_configuration = LoggerConfiguration(console_level='DEBUG' if debug else 'INFO')
    configure_logger(logger_configuration)


@app.command('check')
def _check(
    changes_folder: Annotated[
        Path,
        typer.Option(
            '--changes-folder',
            help='The folder containing the change files.',
            envvar=f'{ENV_VAR_PREFIX}_CHANGES_FOLDER',
        ),
    ] = Path('.changes'),
    branch: Annotated[
        str | None,
        typer.Option(
            '--compare-to-branch',
            help='The git branch to compare changes folder to.',
            envvar=f'{ENV_VAR_PREFIX}_COMPARE_TO_BRANCH',
        ),
    ] = None,
) -> None:
    files = discover_change_files(changes_folder, branch)
    if not files:
        raise typer.Exit(code=1)
    _, errors = validate_change_files(files)
    if errors:
        raise typer.Exit(code=1)


@app.command('release')
def _release(
    changes_folder: Annotated[
        Path,
        typer.Option(
            '--changes-folder',
            help='The folder containing the change files.',
            envvar=f'{ENV_VAR_PREFIX}_CHANGES_FOLDER',
        ),
    ] = Path('.changes'),
    changelog_file: Annotated[
        Path,
        typer.Option(
            '--changelog',
            help='The changelog file path.',
            envvar=f'{ENV_VAR_PREFIX}_CHANGELOG',
        ),
    ] = Path('CHANGELOG.md'),
) -> None:
    files = discover_change_files(changes_folder, None)
    if not files:
        logger.error('❌ Release aborted due to no change files.')
        raise typer.Exit(code=1)
    valid, errors = validate_change_files(files)
    if errors:
        logger.error('❌ Release aborted due to invalid change files.')
        raise typer.Exit(code=1)
    bump_type = get_highest_version_bump(valid.values()).bump_name
    logger.info('Established bump type is: {}', bump_type)
    old_version, new_version = bump_version(bump_spec=bump_type)
    logger.info('Updated version from {} to {}', old_version, new_version)
    remove_files(files)
    add_new_version_to_changelog(
        changelog_file=changelog_file,
        version=new_version,
        changes=list(valid.values()),
    )
    logger.info('✅ Release completed successfully.')


@app.command('show-version')
def _show_version() -> None:
    logger.info(bump_version()[0])


def main() -> None:
    """Load settings and run the application."""
    load_dotenv(ENV_VAR_PREFIX)
    app()


if __name__ == '__main__':
    main()  # pragma: no cover
