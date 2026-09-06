import time
from pathlib import Path

import pytest
from dulwich import porcelain
from dulwich.objects import Blob, Commit, Tree
from dulwich.refs import Ref

from panda_simple_releases._git import (
    _ensure_string,
    _find_common_ancestor_commit,
    _get_commit,
    get_new_files_since_branched_out,
    GitError,
)


class RepoWrapper:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.repo_path_str = str(path)
        self.repo = porcelain.init(self.repo_path_str)
        self.author = b'Test User <test@example.com>'

    def add_file(self, path: str, content: str) -> None:
        file = self.path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        porcelain.add(self.repo, path)

    def commit(self, msg: str) -> None:
        porcelain.commit(
            self.repo,
            message=msg.encode(),
            author=self.author,
            committer=self.author,
        )

    def head(self) -> str:
        return self.repo.head().decode()

    def name_head(self, branch: str, origin: str | None = None) -> None:
        if origin is None:
            self.repo.refs[Ref(f'refs/heads/{branch}'.encode())] = self.repo.head()
        else:
            self.repo.refs[Ref(f'refs/remotes/{origin}/{branch}'.encode())] = self.repo.head()


@pytest.fixture
def repo_wrapper(tmp_path: Path) -> RepoWrapper:
    repo_wrapper = RepoWrapper(tmp_path)
    repo_wrapper.add_file('root_file.txt', 'Some content')
    repo_wrapper.add_file('test-folder/folder_file.txt', 'Some second content')
    repo_wrapper.commit('first')
    repo_wrapper.name_head('initial-commit')
    repo_wrapper.add_file('second_root_file.txt', 'Some second content')
    repo_wrapper.add_file('test-folder/folder_second_file.txt', 'Some more second content')
    repo_wrapper.commit('second')
    repo_wrapper.name_head('fixture-branch')
    return repo_wrapper


def _create_detached_commit(repo_wrapper: RepoWrapper) -> Commit:
    blob = Blob.from_string(b'# new project\n')
    repo_wrapper.repo.object_store.add_object(blob)
    tree = Tree()
    tree.add(b'README.md', 0o100644, blob.id)
    repo_wrapper.repo.object_store.add_object(tree)
    detached_commit = Commit()
    detached_commit.tree = tree.id
    detached_commit.parents = []
    detached_commit.author = detached_commit.committer = b'Twoje Imie <twoj@email.com>'
    detached_commit.commit_time = detached_commit.author_time = int(time.time())
    detached_commit.commit_timezone = detached_commit.author_timezone = 0
    detached_commit.message = b'root commit'
    repo_wrapper.repo.object_store.add_object(detached_commit)
    repo_wrapper.repo[b'refs/heads/separate-branch'] = detached_commit.id
    return detached_commit


def _create_complex_structure(repo_wrapper: RepoWrapper) -> None:
    repo_wrapper.name_head('diverge-point')

    repo_wrapper.add_file('third_root_file.txt', 'Some third content')
    repo_wrapper.add_file('test-folder/folder_third_file.txt', 'Some more third content')
    repo_wrapper.commit('third')
    repo_wrapper.name_head('test-destination')

    porcelain.checkout(repo_wrapper.repo, 'diverge-point', new_branch='feature-branch')

    repo_wrapper.add_file('my_root_feature.txt', 'Feature content')
    repo_wrapper.add_file('test-folder/my_folder_feature.txt', 'Feature more content')
    repo_wrapper.commit('add feature')
    repo_wrapper.name_head('feature-branch-no-merge')
    porcelain.merge(repo_wrapper.repo, 'test-destination')


def test_get_new_files_since_branched_out_not_repo(tmp_path: Path):
    with pytest.raises(GitError):
        get_new_files_since_branched_out('', repo_folder=str(tmp_path))


def test_get_new_files_since_branched_out(repo_wrapper: RepoWrapper):
    _create_complex_structure(repo_wrapper)

    porcelain.checkout(repo_wrapper.repo, 'feature-branch-no-merge')
    assert get_new_files_since_branched_out('test-destination', repo_folder=repo_wrapper.repo_path_str) == [
        Path('my_root_feature.txt'),
        Path('test-folder/my_folder_feature.txt'),
    ]
    assert get_new_files_since_branched_out('initial-commit', repo_folder=repo_wrapper.repo_path_str) == [
        Path('my_root_feature.txt'),
        Path('second_root_file.txt'),
        Path('test-folder/folder_second_file.txt'),
        Path('test-folder/my_folder_feature.txt'),
    ]
    porcelain.checkout(repo_wrapper.repo, 'feature-branch')
    assert get_new_files_since_branched_out('test-destination', repo_folder=repo_wrapper.repo_path_str) == [
        Path('my_root_feature.txt'),
        Path('test-folder/my_folder_feature.txt'),
    ]


def test_find_common_ancestor_commit_no_common(repo_wrapper: RepoWrapper):
    _create_complex_structure(repo_wrapper)
    destination_commit = _get_commit(repo_wrapper.repo, 'test-destination')
    diverge_commit = _get_commit(repo_wrapper.repo, 'diverge-point')
    feature_before_merge_commit = _get_commit(repo_wrapper.repo, 'feature-branch-no-merge')
    feature_commit = _get_commit(repo_wrapper.repo, 'feature-branch')
    detached_commit = _create_detached_commit(repo_wrapper)

    assert (
        _find_common_ancestor_commit(
            repo_wrapper.repo,
            feature_before_merge_commit,
            destination_commit,
        )
        == diverge_commit
    )
    assert (
        _find_common_ancestor_commit(
            repo_wrapper.repo,
            feature_before_merge_commit,
            diverge_commit,
        )
        == diverge_commit
    )
    assert (
        _find_common_ancestor_commit(
            repo_wrapper.repo,
            feature_before_merge_commit,
            diverge_commit,
        )
        == diverge_commit
    )
    assert (
        _find_common_ancestor_commit(
            repo_wrapper.repo,
            feature_commit,
            destination_commit,
        )
        == destination_commit
    )
    with pytest.raises(GitError):
        _find_common_ancestor_commit(
            repo_wrapper.repo,
            detached_commit,
            feature_commit,
        )


def test_get_commit_with_commit_id(repo_wrapper: RepoWrapper):
    commit_id = repo_wrapper.repo.head()
    repo_wrapper.name_head('local-branch')
    repo_wrapper.name_head('remote-branch', 'remote-repo')
    for objectish in (
        commit_id.decode(),
        'local-branch',
        'remote-repo/remote-branch',
        'HEAD',
    ):
        result = _get_commit(repo_wrapper.repo, objectish)
        assert isinstance(result, Commit)
        assert result.id == commit_id

    for objectish in (
        commit_id[:-1].decode(),
        'non-existing-branch',
        'remote-branch',
        'remote-repo/local-branch',
        'remote-repo/non-existing-branch',
        'initial-commit:root_file.txt',
    ):
        with pytest.raises(GitError):
            _get_commit(repo_wrapper.repo, objectish)


@pytest.mark.parametrize(
    ['value', 'expected_output'],
    [
        ('', ''),
        ('zonk', 'zonk'),
        (b'', ''),
        (b'zonk', 'zonk'),
    ],
)
def test_ensure_string(value: str | bytes, expected_output: str):
    assert _ensure_string(value) == expected_output
