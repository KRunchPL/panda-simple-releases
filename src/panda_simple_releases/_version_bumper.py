# pragma: no cover
from pathlib import Path

# import hatch_semver to ensure that the hatch_semver plugin is loaded, even if it is not used directly
import hatch_semver  # type: ignore [import-untyped]  # noqa: F401
import tomlkit
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManager
from hatchling.version.scheme.standard import StandardScheme


def bump_version(*, bump_spec: str = '', project_root: Path | None = None) -> tuple[str, str]:
    """
    Bump the project version according to provided specification.

    :param bump_spec: The version bump specification, e.g., 'major', 'minor', 'patch', or a specific version
                      string. When empty, the version will not be changed.
    :param project_root: The root directory of the project, defaults to CWD.
    :return: A tuple containing the original version and the updated version.
    """
    project_root = project_root or Path.cwd()
    metadata = _load_metadata(project_root)

    if 'version' in metadata.config.get('project', {}):
        return _handle_hardcoded_version(bump_spec, project_root)
    return _handle_dynamic_version(bump_spec, metadata)


def _load_metadata(project_root: Path) -> ProjectMetadata[PluginManager]:
    plugin_manager = PluginManager()
    return ProjectMetadata(str(project_root), plugin_manager)


def _handle_hardcoded_version(bump_spec: str, project_root: Path) -> tuple[str, str]:
    project_file_path = project_root / 'pyproject.toml'

    with project_file_path.open(encoding='utf-8') as fr:
        raw_config = tomlkit.parse(fr.read())
    original_version = raw_config['project']['version']

    if not bump_spec:
        return original_version, original_version

    scheme = StandardScheme(str(project_root), {})
    updated_version = scheme.update(bump_spec, original_version, {})
    raw_config['project']['version'] = updated_version
    with project_file_path.open('w', encoding='utf-8') as fw:
        fw.write(tomlkit.dumps(raw_config))
    return original_version, updated_version


def _handle_dynamic_version(bump_spec: str, metadata: ProjectMetadata[PluginManager]) -> tuple[str, str]:
    source = metadata.hatch.version.source
    version_data = source.get_version_data()
    original_version: str = version_data['version']

    if not bump_spec:
        return original_version, original_version

    updated_version = metadata.hatch.version.scheme.update(bump_spec, original_version, version_data)
    source.set_version(updated_version, version_data)
    return original_version, updated_version
