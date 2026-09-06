from datetime import datetime, UTC
from pathlib import Path

from ._change import Change


def add_new_version_to_changelog(
    *,
    changelog_file: Path,
    version: str,
    changes: list[Change],
) -> None:
    entry = _generate_changelog_entry(version, changes)
    _insert_into_changelog(changelog_file, entry)


def _generate_changelog_entry(version: str, changes: list[Change]) -> str:
    if not changes:
        msg = f'Cannot generate changelog entry for version "{version}" with no changes.'
        raise ValueError(msg)

    dev_entries = []
    prod_entries = []
    for change in changes:
        entry = _generate_change_string(change)
        if change.change_type.is_dev:
            dev_entries.append(entry)
        else:
            prod_entries.append(entry)
    prod_text = '\n\n'.join(prod_entries)
    dev_text = '\n\n'.join(dev_entries)
    changelog_lines = [
        f'## [{version}] - {datetime.now(UTC).date().isoformat()}',
        '',
    ]
    if prod_text:
        changelog_lines.append(prod_text)
        changelog_lines.append('')
    if dev_text:
        changelog_lines.append('### Development')
        changelog_lines.append('')
        changelog_lines.append(dev_text)

    return '\n'.join(changelog_lines).strip()


def _generate_change_string(change: Change) -> str:
    lines = [
        f'- {change.title}',
    ]
    if change.description:
        lines.append('')
        lines.extend(
            f'    {description_line}' if description_line else '' for description_line in change.description
        )
    return '\n'.join(lines)


_DEFAULT_CHANGELOG_CONTENT = """\
# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{new_section}
"""


def _insert_into_changelog(changelog_file: Path, new_section: str) -> None:
    if not changelog_file.exists():
        changelog_file.write_text(
            _DEFAULT_CHANGELOG_CONTENT.format(new_section=new_section),
            encoding='utf-8',
        )
        return
    lines = changelog_file.read_text(encoding='utf-8').splitlines(keepends=True)

    first_release_idx = next(
        (index for index, line in enumerate(lines) if line.startswith('## [')),
        None,
    )

    if first_release_idx is None:
        with changelog_file.open('a', encoding='utf-8') as file:
            file.write(f'\n{new_section}\n')
        return

    before_releases = ''.join(lines[:first_release_idx]).rstrip()
    from_releases = ''.join(lines[first_release_idx:]).rstrip()
    changelog_file.write_text(
        f'{before_releases}\n\n{new_section}\n\n{from_releases}\n',
        encoding='utf-8',
    )
