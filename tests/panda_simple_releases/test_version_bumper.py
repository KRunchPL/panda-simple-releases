from pathlib import Path
from typing import Any, Literal

import pytest
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManager
from pytest_mock import MockerFixture

from panda_simple_releases._version_bumper import (
    _handle_dynamic_version,
    _handle_hardcoded_version,
    _load_metadata,
    bump_version,
)


_TESTED_MODULE = bump_version.__module__


@pytest.mark.parametrize('project_root', [None, Path('some/path')])
def test_bump_version_uses_proper_project_root(mocker: MockerFixture, project_root: Path | None):
    if project_root is None:
        expected_project_root = Path.cwd()
        cwd_mock = mocker.patch(_TESTED_MODULE + '.Path.cwd', return_value=expected_project_root)
    else:
        expected_project_root = project_root
        cwd_mock = mocker.patch(_TESTED_MODULE + '.Path.cwd')
    hardcoded_mock = mocker.patch(_TESTED_MODULE + '._handle_hardcoded_version')
    load_metadata_mock = mocker.patch(_TESTED_MODULE + '._load_metadata')
    load_metadata_mock.return_value.config = {'project': {'version': '1.0.0'}}

    bump_version(project_root=project_root)

    if project_root is not None:
        cwd_mock.assert_not_called()
    else:
        cwd_mock.assert_called_once_with()
    load_metadata_mock.assert_called_once_with(expected_project_root)
    hardcoded_mock.assert_called_once_with('', expected_project_root)


@pytest.mark.parametrize(
    ['config', 'hardcoded_vs_dynamic'],
    [
        ({'project': {'version': '1.0.0'}}, 'hardcoded'),
        ({}, 'dynamic'),
        ({'project': {'dynamic': ['version']}}, 'dynamic'),
    ],
)
@pytest.mark.parametrize(['bump_spec', 'expected_bump_spec'], [(None, ''), ('', ''), ('some', 'some')])
def test_bump_version_logic(
    mocker: MockerFixture,
    config: dict[str, Any],
    hardcoded_vs_dynamic: Literal['hardcoded', 'dynamic'],
    bump_spec: str | None,
    expected_bump_spec: str,
):
    load_metadata_mock = mocker.patch(_TESTED_MODULE + '._load_metadata')
    load_metadata_mock.return_value.config = config
    hardcoded_mock = mocker.patch(_TESTED_MODULE + '._handle_hardcoded_version')
    dynamic_mock = mocker.patch(_TESTED_MODULE + '._handle_dynamic_version')

    result = bump_version() if bump_spec is None else bump_version(bump_spec=bump_spec)

    match hardcoded_vs_dynamic:
        case 'hardcoded':
            hardcoded_mock.assert_called_once_with(expected_bump_spec, Path.cwd())
            dynamic_mock.assert_not_called()
            assert result is hardcoded_mock.return_value
        case 'dynamic':
            dynamic_mock.assert_called_once_with(expected_bump_spec, load_metadata_mock.return_value)
            hardcoded_mock.assert_not_called()
            assert result is dynamic_mock.return_value


@pytest.mark.parametrize(['project_root', 'expected_param'], [(Path('abc'), 'abc'), (Path('def'), 'def')])
def test_load_metadata(mocker: MockerFixture, project_root: Path, expected_param: str) -> None:
    plugin_manager_mock = mocker.patch(_TESTED_MODULE + '.PluginManager')
    project_metadata_mock = mocker.patch(_TESTED_MODULE + '.ProjectMetadata')

    result = _load_metadata(project_root)

    plugin_manager_mock.assert_called_once_with()
    project_metadata_mock.assert_called_once_with(expected_param, plugin_manager_mock.return_value)
    assert result is project_metadata_mock.return_value


@pytest.fixture
def hardcoded_project_root(tmp_path: Path) -> Path:
    (tmp_path / 'pyproject.toml').write_text(
        '[project]\nversion = "1.0.0"\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.mark.parametrize(
    ['bump_spec', 'expected_updated_version'],
    [
        ('minor', '1.1.0'),
        ('patch', '1.0.1'),
        ('major', '2.0.0'),
        ('4.1.3', '4.1.3'),
        ('', '1.0.0'),
    ],
)
def test_handle_hardcoded_version(
    hardcoded_project_root: Path,
    bump_spec: str,
    expected_updated_version: str,
) -> None:
    original_version, updated_version = _handle_hardcoded_version(
        bump_spec,
        hardcoded_project_root,
    )

    assert original_version == '1.0.0'
    assert updated_version == expected_updated_version
    pyproject_content = (hardcoded_project_root / 'pyproject.toml').read_text(encoding='utf-8')
    assert f'version = "{expected_updated_version}"' in pyproject_content


_DYNAMIC_PYPROJECT_CONTENT = """\
[project]
dynamic = ["version"]


[tool.hatch.version]
scheme = "semver"
path = "version.txt"
pattern = "(?P<version>.*)"
"""


@pytest.fixture
def dynamic_project_metadata(tmp_path: Path) -> ProjectMetadata[PluginManager]:
    (tmp_path / 'version.txt').write_text(
        '1.0.0',
        encoding='utf-8',
    )
    (tmp_path / 'pyproject.toml').write_text(
        _DYNAMIC_PYPROJECT_CONTENT,
        encoding='utf-8',
    )
    return _load_metadata(tmp_path)


@pytest.mark.parametrize(
    ['bump_spec', 'expected_updated_version'],
    [
        ('minor', '1.1.0'),
        ('patch', '1.0.1'),
        ('major', '2.0.0'),
        ('4.1.3', '4.1.3'),
        ('', '1.0.0'),
    ],
)
def test_handle_dynamic_version(
    dynamic_project_metadata: ProjectMetadata[PluginManager],
    bump_spec: str,
    expected_updated_version: str,
) -> None:
    original_version, updated_version = _handle_dynamic_version(
        bump_spec,
        dynamic_project_metadata,
    )

    assert original_version == '1.0.0'
    assert updated_version == expected_updated_version
    version_content = (Path(dynamic_project_metadata.root) / 'version.txt').read_text(encoding='utf-8')
    assert expected_updated_version == version_content
