from unittest.mock import call, MagicMock

import pytest
from panda_pytest_assertions.assert_context import assert_context
from panda_pytest_assertions.assert_object import assert_object, ObjectAttributes, with_type
from pytest_mock import MockerFixture

from panda_simple_releases._change import Change, ChangeType
from panda_simple_releases._change_parser import (
    _parse_description,
    _parse_title_line,
    _validate_line_after_title,
    _validate_non_empty,
    ChangeParserError,
    parse_change_from_string,
)


_TESTED_MODULE = ChangeParserError.__module__


def test_parse_change_from_string(mocker: MockerFixture):
    change_id = 'my_change_id'
    change_string = """\

   line a

   line b
   line c



"""
    lines = [
        'line a',
        '',
        '   line b',
        '   line c',
    ]
    change_type = ChangeType.FEATURE
    scope = 'my_scope'
    title = 'my_title'
    description = ['line 1', '', 'line 2']
    mock = MagicMock()
    for function_name, return_value in (
        ('_validate_non_empty', None),
        ('_parse_title_line', (change_type, scope, title)),
        ('_validate_line_after_title', None),
        ('_parse_description', description),
    ):
        mock.attach_mock(
            mocker.patch(_TESTED_MODULE + f'.{function_name}', return_value=return_value),
            function_name,
        )

    result = parse_change_from_string(change_id, change_string)

    assert_object(
        expectation=with_type(Change)(
            ObjectAttributes({
                'change_type': change_type,
                'scope': scope,
                'title': title,
                'description': description,
            }),
        ),
        object_=result,
    )

    assert mock.mock_calls == [
        call._validate_non_empty(change_id, lines),
        call._parse_title_line(change_id, lines),
        call._validate_line_after_title(change_id, lines),
        call._parse_description(change_id, lines),
    ]


@pytest.mark.parametrize(
    ['lines', 'expected_exception'],
    [
        ([], ChangeParserError),
        ([''], None),
        (['', ''], None),
        (['   '], None),
        (['  ', '   '], None),
    ],
)
def test_validate_non_empty(lines: list[str], expected_exception: type[Exception] | None):
    with assert_context(exception=expected_exception):
        _validate_non_empty('', lines)


@pytest.mark.parametrize(
    ['lines', 'expected'],
    [
        (
            ['feat: abc'],
            (ChangeType.FEAT, None, 'abc'),
        ),
        (
            ['feat:\tabc'],
            (ChangeType.FEAT, None, 'abc'),
        ),
        (
            ['chore-skip: this is some long description'],
            (ChangeType.CHORE_SKIP, None, 'this is some long description'),
        ),
        (
            ['chore-skip:       description    to be stripped          '],
            (ChangeType.CHORE_SKIP, None, 'description    to be stripped'),
        ),
        (
            ['chore-skip: description with !@#$%^&*()"\'\\'],
            (ChangeType.CHORE_SKIP, None, 'description with !@#$%^&*()"\'\\'),
        ),
        (
            ['breaking(ice cream scope): abc'],
            (ChangeType.BREAKING, 'ice cream scope', 'abc'),
        ),
        (
            ['breaking(    with spaces\t\t): abc'],
            (ChangeType.BREAKING, 'with spaces', 'abc'),
        ),
        (
            ['breaking(with @@^*!&#((;): abc'],
            (ChangeType.BREAKING, 'with @@^*!&#((;', 'abc'),
        ),
        (
            ['breaking((xyz): abc'],
            (ChangeType.BREAKING, '(xyz', 'abc'),
        ),
        (
            ['feat(): abc'],
            (ChangeType.FEAT, None, 'abc'),
        ),
        (
            ['feat(   ): abc'],
            (ChangeType.FEAT, None, 'abc'),
        ),
    ],
)
def test_parse_title_line_valid(lines: list[str], expected: tuple[ChangeType, str | None, str]):
    assert _parse_title_line('', lines) == expected


@pytest.mark.parametrize(
    'lines',
    [
        [''],
        ['feat abc'],
        ['unknown: abc'],
        ['FEAT: abc'],
        ['feat:'],
        ['feat:abc'],
        ['feat : abc'],
        [': abc'],
        ['feat:   '],
        ['feat(xyz):   '],
        ['feat(xyz):'],
        ['feat(xyz) abc'],
        ['feat(xyz)): abc'],
        ['feat(xyz: abc'],
        ['feat(xyz):abc'],
        ['feat (xyz): abc'],
        ['feat xyz): abc'],
    ],
)
def test_parse_title_line_invalid(lines: list[str]):
    with pytest.raises(ChangeParserError):
        _parse_title_line('', lines)


@pytest.mark.parametrize(
    ['lines', 'expected_exception'],
    [
        ([], None),
        ([''], None),
        (['', ''], None),
        (['', '', 'abc', ''], None),
        (['', '   '], None),
        (['', '   ', 'abc'], None),
        (['', 'abc'], ChangeParserError),
        (['', 'abc', ''], ChangeParserError),
        (['', 'abc', '  '], ChangeParserError),
    ],
)
def test_validate_line_after_title(lines: list[str], expected_exception: type[Exception] | None):
    with assert_context(exception=expected_exception):
        _validate_line_after_title('', lines)


@pytest.mark.parametrize(
    ['lines', 'expected_description'],
    [
        ([], []),
        ([''], []),
        (['', ''], []),
        (['', '', ''], []),
        (['', '', '', ''], []),
        (
            [
                '',
                '',
                'single line',
            ],
            ['single line'],
        ),
        (
            [
                '',
                '',
                '',
                '',
                'single line',
                '',
                '',
            ],
            ['single line'],
        ),
        (
            [
                '',
                '',
                '          single line     ',
            ],
            ['          single line'],
        ),
        (
            [
                '',
                '',
                '',
                '',
                ' first line   ',
                '    ',
                '  second line    ',
                '',
                '',
            ],
            [
                ' first line',
                '',
                '  second line',
            ],
        ),
    ],
)
def test_parse_description(lines: list[str], expected_description: list[str]):
    assert _parse_description('', lines) == expected_description


def test_change_parser_error():
    change_id = 'some change id'
    message = 'some error msg'
    err = ChangeParserError(change_id, message)
    assert err.change_id == change_id
    assert err.message == message
    assert str(err) == f'Error parsing change file "{change_id}": {message}'
