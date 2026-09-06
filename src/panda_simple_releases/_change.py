from collections.abc import Iterable
from enum import IntEnum, StrEnum
from typing import Self, TYPE_CHECKING

from pydantic import BaseModel


class Change(BaseModel):
    """Change entry."""

    change_type: ChangeType
    scope: str | None
    title: str
    description: list[str]


class VersionBump(IntEnum):
    MAJOR = (4, 'major')
    MINOR = (3, 'minor')
    PATCH = (2, 'patch')
    SKIP = (1, 'skip')

    if TYPE_CHECKING:
        bump_name: str

    def __new__(cls, value: int, bump_name: str | None = None) -> Self:
        if bump_name is None:  # pragma: no cover
            msg = f'VersionBump "{value}" must have a bump_name associated with it.'
            raise RuntimeError(msg)
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.bump_name = bump_name
        return obj


class ChangeType(StrEnum):
    BREAKING = ('breaking', VersionBump.MAJOR)
    MAJOR = ('major', VersionBump.MAJOR)
    FEAT = ('feat', VersionBump.MINOR)
    FEATURE = ('feature', VersionBump.MINOR)
    MINOR = ('minor', VersionBump.MINOR)
    FIX = ('fix', VersionBump.PATCH)
    BUGFIX = ('bugfix', VersionBump.PATCH)
    HOTFIX = ('hotfix', VersionBump.PATCH)
    PATCH = ('patch', VersionBump.PATCH)
    PERF = ('perf', VersionBump.PATCH)
    PERFORMANCE = ('performance', VersionBump.PATCH)
    CHORE = ('chore', VersionBump.PATCH)
    CHORE_SKIP = ('chore-skip', VersionBump.SKIP)
    SKIP = ('skip', VersionBump.SKIP)

    if TYPE_CHECKING:
        version_bump: VersionBump

    def __new__(cls, value: str, version_bump: VersionBump | None = None) -> Self:
        if version_bump is None:  # pragma: no cover
            msg = f'ChangeType "{value}" must have a version_bump associated with it.'
            raise RuntimeError(msg)
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.version_bump = version_bump
        return obj

    @property
    def is_dev(self) -> bool:
        return self in (ChangeType.CHORE, ChangeType.CHORE_SKIP)


def get_highest_version_bump(changes: Iterable[Change]) -> VersionBump:
    """
    Get the highest version bump from a list of changes.

    :param changes: An iterable of Change objects.
    :return: The highest VersionBump found in the changes.
    """
    return max((change.change_type.version_bump for change in changes), default=VersionBump.SKIP)
