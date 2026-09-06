from unittest.mock import MagicMock

import pytest

from panda_simple_releases._file_remover import remove_files


@pytest.mark.parametrize('files_count', [3, 1, 0])
def test_remove_files(files_count: int):
    unlink_mock = MagicMock()

    class RemovableFileMock(MagicMock):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.unlink = unlink_mock

    files = [RemovableFileMock() for _ in range(files_count)]

    remove_files(files)

    assert unlink_mock.call_count == files_count
