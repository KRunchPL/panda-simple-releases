import pytest
from munch import Munch
from pydantic import ValidationError

from panda_simple_releases._change import Change, ChangeType, get_highest_version_bump, VersionBump


def test_change_all_fields_required():
    with pytest.raises(ValidationError) as exc_info:
        Change.model_validate({})
    assert [(error['type'], error['loc']) for error in exc_info.value.errors()] == [
        ('missing', ('change_type',)),
        ('missing', ('scope',)),
        ('missing', ('title',)),
        ('missing', ('description',)),
    ]


@pytest.mark.parametrize(
    ['value', 'expected_version_bump'],
    [
        (3, VersionBump.MINOR),
        (1, VersionBump.SKIP),
    ],
)
def test_version_bump_is_int(value: int, expected_version_bump: VersionBump):
    version_bump = VersionBump(value)
    assert version_bump is expected_version_bump
    assert version_bump == value


@pytest.mark.parametrize(
    ['version_bump', 'expected_value'],
    [
        (VersionBump.MINOR, 'minor'),
        (VersionBump.SKIP, 'skip'),
    ],
)
def test_version_bump_bump_name(version_bump: VersionBump, expected_value: str):
    assert version_bump.bump_name == expected_value


@pytest.mark.parametrize(
    ['value', 'expected_change_type'],
    [
        ('patch', ChangeType.PATCH),
        ('chore-skip', ChangeType.CHORE_SKIP),
    ],
)
def test_change_type_is_str(value: str, expected_change_type: ChangeType):
    change_type = ChangeType(value)
    assert change_type is expected_change_type
    assert change_type == value


@pytest.mark.parametrize(
    ['change_type', 'expected_value'],
    [
        (ChangeType.PATCH, VersionBump.PATCH),
        (ChangeType.CHORE_SKIP, VersionBump.SKIP),
    ],
)
def test_change_type_version_bump(change_type: ChangeType, expected_value: VersionBump):
    assert change_type.version_bump == expected_value


@pytest.mark.parametrize(
    ['change_type', 'expected_value'],
    [
        (ChangeType.PATCH, False),
        (ChangeType.CHORE, True),
    ],
)
def test_change_type_is_dev(change_type: ChangeType, expected_value: bool):
    assert change_type.is_dev == expected_value


@pytest.mark.parametrize(
    ['change_types', 'expected_value'],
    [
        ([], VersionBump.SKIP),
        ([ChangeType.FEATURE], VersionBump.MINOR),
        ([ChangeType.BREAKING, ChangeType.MAJOR], VersionBump.MAJOR),
        ([ChangeType.BREAKING, ChangeType.FEATURE], VersionBump.MAJOR),
        ([ChangeType.BREAKING, ChangeType.PERF], VersionBump.MAJOR),
        ([ChangeType.BREAKING, ChangeType.CHORE_SKIP], VersionBump.MAJOR),
        ([ChangeType.FEATURE, ChangeType.FEATURE], VersionBump.MINOR),
        ([ChangeType.FEATURE, ChangeType.PERF], VersionBump.MINOR),
        ([ChangeType.FEATURE, ChangeType.CHORE_SKIP], VersionBump.MINOR),
        ([ChangeType.PERF, ChangeType.PERF], VersionBump.PATCH),
        ([ChangeType.PERF, ChangeType.CHORE_SKIP], VersionBump.PATCH),
        ([ChangeType.SKIP, ChangeType.CHORE_SKIP], VersionBump.SKIP),
    ],
)
def test_get_highest_version_bump(change_types: list[ChangeType], expected_value: VersionBump):
    changes: list[Change] = [Munch(change_type=change_type) for change_type in change_types]  # type: ignore [misc]
    assert get_highest_version_bump(changes) == expected_value
