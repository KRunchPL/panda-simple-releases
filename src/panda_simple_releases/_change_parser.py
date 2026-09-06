import re

from loguru import logger

from ._change import Change, ChangeType


def parse_change_from_string(change_id: str, change_string: str) -> Change:
    """
    Create a Change instance from a string.

    :param change_id: The ID of the change.
    :param change_string: The string representing the change.
    :return: A Change instance.
    """
    logger.debug('[{}] Starting validation', change_id)
    lines = change_string.strip().splitlines()
    _validate_non_empty(change_id, lines)
    change_type, scope, title = _parse_title_line(change_id, lines)
    _validate_line_after_title(change_id, lines)
    description = _parse_description(change_id, lines)
    logger.debug('  ✅ [{}] Change Valid', change_id)
    return Change(
        change_type=change_type,
        scope=scope,
        title=title,
        description=description,
    )


def _validate_non_empty(change_id: str, lines: list[str]) -> None:
    if len(lines) == 0:
        logger.debug('  ❌ [{}] Change is empty', change_id)
        raise ChangeParserError(change_id, 'The change is empty')
    logger.debug('  [{}] Change is not empty', change_id)


_TITLE_LINE_REGEX = re.compile(r'^(?P<change_type>[a-z-]+)(\((?P<scope>[^)]*)\))?:[ \t](?P<title>.+)$')


def _parse_title_line(change_id: str, lines: list[str]) -> tuple[ChangeType, str | None, str]:
    title_line = lines[0].strip()
    logger.debug('  [{}] Title line: "{}"', change_id, title_line)
    if not (title_line_match := _TITLE_LINE_REGEX.match(title_line)):
        logger.debug('  ❌ [{}] Title line invalid', change_id)
        raise ChangeParserError(
            change_id,
            (
                f'Title line does not match required format. '
                f'Got: "{title_line}". '
                f'Expected: "<change_type>: <message> or <change_type>(<scope>): <message>".'
            ),
        )
    change_type = title_line_match.group('change_type')
    logger.debug('  [{}] Change type: "{}"', change_id, change_type)
    if change_type not in ChangeType:
        logger.debug('  ❌ [{}] Change type invalid', change_id)
        raise ChangeParserError(
            change_id,
            f'Invalid change type. Got: "{change_type}". Expected one of: {VALID_CHANGE_TYPES}.',
        )
    scope = (title_line_match.group('scope') or '').strip() or None
    logger.debug('  [{}] Scope: "{}"', change_id, scope)
    title = title_line_match.group('title').strip()
    logger.debug('  [{}] Title: "{}"', change_id, title)
    return ChangeType(change_type), scope, title


def _validate_line_after_title(change_id: str, lines: list[str]) -> None:
    if len(lines) > 1 and (second_line := lines[1].strip()) != '':
        logger.debug('  ❌ [{}] Non empty line after the title line', change_id)
        raise ChangeParserError(
            change_id,
            f'Line after the title line must be blank. Got: "{second_line}".',
        )
    logger.debug('  [{}] Found empty line after title line', change_id)


def _parse_description(change_id: str, lines: list[str]) -> list[str]:
    description = lines[2:]
    for line_index, description_line in enumerate(description):
        if description_line.strip() != '':
            description = description[line_index:]
            break
    else:
        description = []
    for line_index, description_line in enumerate(reversed(description)):
        if description_line.strip() != '':
            description = description[: len(description) - line_index]
            break
    else:
        description = []
    for line_index, description_line in enumerate(description):
        if description_line.strip() == '':
            description[line_index] = ''
        else:
            description[line_index] = description_line.rstrip()

    logger.debug('  [{}] Description: "{}"', change_id, description)
    return description


class ChangeParserError(Exception):
    """
    Raised when a change string cannot be parsed.

    :param change_id: The ID of the change.
    :param message: The error message.
    """

    def __init__(self, change_id: str, message: str) -> None:
        self.change_id = change_id
        self.message = message
        super().__init__(f'Error parsing change file "{change_id}": {message}')


REQUIRED_CHANGE_FORMAT = """\
Line 1: <change_type>: <message> or <change_type>(<scope>): <message>
Line 2: (blank line)
Line 3+: (optional) <description>"""

EXAMPLE_CHANGE = """\
feat: Add new feature

This feature does something really cool.
It has multiple lines in the description."""

VALID_CHANGE_TYPES = ', '.join(ChangeType)
