# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-06

Initial release. Implementing 3 commands.

* **`panda-simple-releases check`**

    Validates that `.changes/` contains at least one correctly formatted change file.

    *Tip: Use `--compare-to-branch <branch_name>` in PR pipelines. With this flag, the tool verifies that a new change file was added and validates **only** the files newly added to your current branch.*

* **`panda-simple-releases release`**

    Validates change files, determines the appropriate version bump (major, minor, or patch), updates the version, removes the change files, and updates `CHANGELOG.md`.

* **`panda-simple-releases show-version`**

    Outputs the current project version. Useful for generating release commit messages or tags.
