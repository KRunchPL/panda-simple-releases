from collections.abc import Iterable
from pathlib import Path


def remove_files(files: Iterable[Path]) -> None:
    """
    Remove the given files.

    :param files: An iterable of Path objects representing the files to remove.
    """
    for file in files:
        file.unlink(missing_ok=True)
