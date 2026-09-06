from pathlib import Path

from loguru import logger

from ._change import Change
from ._change_parser import (
    ChangeParserError,
    EXAMPLE_CHANGE,
    parse_change_from_string,
    REQUIRED_CHANGE_FORMAT,
    VALID_CHANGE_TYPES,
)


def validate_change_files(change_files: list[Path]) -> tuple[dict[str, Change], dict[str, str]]:
    """
    Validate all change files.

    :param change_files: List of change files to validate.
    :return: tuple of (valid changes, errors)
    """
    valid: dict[str, Change] = {}
    errors: dict[str, str] = {}
    for change_file in change_files:
        try:
            valid[change_file.name] = _parse_change_file(change_file)
        except ChangeParserError as e:
            errors[change_file.name] = e.message
    if not errors:
        logger.info('✅ All {} change file(s) are valid.', len(valid))
        return valid, errors
    if valid:
        logger.warning(
            '⚠️ Only {} out of {} change file(s) are valid: {}.',
            len(valid),
            len(change_files),
            ', '.join(f'"{file_name}"' for file_name in valid),
        )
    logger.error(
        '❌ {} out of {} change file(s) are invalid. Errors:',
        len(errors),
        len(change_files),
    )
    for file_name, error in errors.items():
        logger.error('  - "{}": {}', file_name, error)
    logger.info('Required format:\n---\n{}\n---\n', REQUIRED_CHANGE_FORMAT)
    logger.info('Valid change types: {}\n', VALID_CHANGE_TYPES)
    logger.info('Example change:\n---\n{}\n---\n', EXAMPLE_CHANGE)
    return valid, errors


def _parse_change_file(file_path: Path) -> Change:
    return parse_change_from_string(file_path.name, file_path.read_text(encoding='utf-8'))
