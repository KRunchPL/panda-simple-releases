import importlib.metadata

import typer


def version_callback(package_name: str, version_flag: bool) -> None:  # noqa: FBT001
    """
    Display the version of the application when the version flag is used.

    :param package_name: The name of the package for which to display the version.
    :param version_flag: Boolean indicating if the version flag was provided.
    """
    if not version_flag:
        return
    try:
        version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        version = 'unknown'
    typer.echo(f'{package_name} version {version}')
    raise typer.Exit
