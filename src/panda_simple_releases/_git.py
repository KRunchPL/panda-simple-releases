import stat
from pathlib import Path

from dulwich.diff_tree import walk_trees
from dulwich.errors import NotGitRepository
from dulwich.graph import find_merge_base
from dulwich.objects import Commit
from dulwich.objectspec import parse_object
from dulwich.repo import Repo


class GitError(Exception):
    """Raised when there is a problem with git repository."""


def get_new_files_since_branched_out(branch: str, repo_folder: str = '.') -> list[Path]:
    """
    Find all file that were added in git since HEAD was branched out from `branch`.

    git diff --name-only --diff-filter=A "branch...HEAD"

    :param branch: branch to compare to
    :param repo_folder: optional path of the repo to work on (by default cwd)
    :return: list of new files paths
    """
    try:
        repo = Repo(repo_folder)
    except NotGitRepository:
        msg = 'Current working directory is not a git repository.'
        raise GitError(msg) from None
    with repo:
        dest_commit = _get_commit(repo, branch)
        head_commit = _get_commit(repo, 'HEAD')
        common_ancestor_commit = _find_common_ancestor_commit(repo, dest_commit, head_commit)
        changed_files = [
            change[1].path.decode()
            for change in walk_trees(repo.object_store, common_ancestor_commit.tree, head_commit.tree)
            if not change[0] and change[1] and not stat.S_ISDIR(change[1].mode)
        ]
    return [Path(file) for file in changed_files]


def _get_commit(repo: Repo, objectish: bytes | str) -> Commit:
    try:
        sha_file = parse_object(repo, objectish)
    except KeyError, AssertionError:
        msg = f'Could not find commit for reference: "{_ensure_string(objectish)}".'
        raise GitError(msg) from None
    if not isinstance(sha_file, Commit):
        msg = f'Object for reference: "{_ensure_string(objectish)}" is not a commit.'
        raise GitError(msg) from None
    return sha_file


def _find_common_ancestor_commit(repo: Repo, commit_1: Commit, commit_2: Commit) -> Commit:
    if not (merge_base_ids := find_merge_base(repo, [commit_1.id, commit_2.id])):
        msg = f'Could not find common ancestor for commits: {commit_1.id.decode()} and {commit_2.id.decode()}'
        raise GitError(msg) from None
    return _get_commit(repo, merge_base_ids[0])


def _ensure_string(value: str | bytes) -> str:
    if isinstance(value, str):
        return value
    return value.decode()
