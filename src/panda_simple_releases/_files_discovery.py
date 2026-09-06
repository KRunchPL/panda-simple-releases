from collections.abc import Generator
from pathlib import Path

from loguru import logger

from ._git import get_new_files_since_branched_out, GitError


def discover_change_files(changes_folder: Path, branch: str | None) -> list[Path]:
    """
    Discover all direct, non-hidden files of a given folder.

    :param changes_folder: The folder to search for files.
    :param branch: If set only files added since HEAD was branched out from `branch` will be considered.
    :return: Paths of the discovered files.
    """
    change_files: list[Path]
    if not changes_folder.exists():
        logger.warning('Path "{}" does not exist', changes_folder.absolute())
        change_files = []
    elif not changes_folder.is_dir():
        logger.error('Path "{}" is not a directory', changes_folder.absolute())
        change_files = []
    elif branch is None:
        change_files = list(_get_change_files_from_folder(changes_folder))
    else:
        change_files = list(_get_change_files_from_git(changes_folder, branch))
    if not change_files:
        logger.error('❌ No change files found.')
    else:
        logger.info(
            'Found {} change file(s): {}.',
            len(change_files),
            ', '.join(f'"{change_file.name}"' for change_file in change_files),
        )
    return change_files


def _get_change_files_from_git(changes_folder: Path, branch: str) -> Generator[Path]:
    logger.info(
        'Looking for change files in "{}" that were added since branching out from "{}"...',
        changes_folder.absolute(),
        branch,
    )
    try:
        git_added_files = get_new_files_since_branched_out(branch)
    except GitError as exc:
        logger.error('❌ Could not fetch change files from git. Error: {}', exc)
        return
    changes_folder = changes_folder.absolute()
    for git_added_file in git_added_files:
        if git_added_file.absolute().parent != changes_folder:
            continue
        if git_added_file.name.startswith('.'):
            logger.debug('Ignoring hidden file: "{}"', git_added_file.name)
            continue
        yield git_added_file


def _get_change_files_from_folder(changes_folder: Path) -> Generator[Path]:
    logger.info('Looking for change files in "{}"...', changes_folder.absolute())
    for child in changes_folder.iterdir():
        if not child.is_file():
            continue
        if child.name.startswith('.'):
            logger.debug('Ignoring hidden file: "{}"', child.name)
            continue
        yield child
