# panda-simple-releases

A lightweight Python CLI tool to simplify the release process and changelog management.

Tools like [Semantic Release](https://semantic-release.org/) are fantastic, and I highly recommend exploring them — they are the right choice for many projects. `panda-simple-releases` is partially inspired by them but deliberately offers a much smaller feature set. It serves as a minimal, file-based alternative for simpler Python projects where full-fledged release frameworks feel too heavy.

## How it Works

1. **Record Changes:** For every change, you create a text file in the `.changes/` directory detailing the change type, title, and description (see [Change File Format](#change-file-format)). CI/CD pipelines can enforce this via the `check` command.
2. **Release:** When you are ready to release, the tool reads and deletes these files, automatically bumps the project version, and adds the new release entry to `CHANGELOG.md`.

*Note: This tool assumes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and relies on [`hatchling`](https://hatch.pypa.io/latest/) with the [`hatch-semver`](https://fleetingbytes.github.io/hatch-semver/) plugin to manage the project version.*

## Usage

The recommended way to run this application is via [`uvx`](https://docs.astral.sh/uv/guides/tools/):

```console
uvx panda-simple-releases --help
```

### Commands

* **`panda-simple-releases check`**

    Validates that `.changes/` contains at least one correctly formatted change file.

    *Tip: Use `--compare-to-branch <branch_name>` in PR pipelines. With this flag, the tool verifies that a new change file was added and validates **only** the files newly added to your current branch.*

* **`panda-simple-releases release`**

    Validates change files, determines the appropriate version bump (major, minor, or patch), updates the version, removes the change files, and updates `CHANGELOG.md`.

* **`panda-simple-releases show-version`**

    Outputs the current project version. Useful for generating release commit messages or tags.

## Change File Format

Change files follow a strict format structurally similar to Conventional Commits:

```text
<change_type>[(<scope>)]: <title>

[optional multi-line description]
```

### Rules

1. **Title (Line 1):** Must start with a valid `<change_type>`, an optional `(<scope>)`, a colon (`:`), a single space, and a brief `<title>`.
2. **Blank Line (Line 2):** If providing a description, the second line **must** be completely blank.
3. **Description (Line 3+):** Optional, multi-line details about the change. Leading and trailing empty lines are automatically stripped.

### Valid Change Types

The `<change_type>` determines how the version will be bumped:

* **Major (X.0.0) - Breaking Changes:** `breaking`, `major`
* **Minor (0.X.0) - Features:** `feat`, `feature`, `minor`
* **Patch (0.0.X) - Fixes & Maintenance:** `fix`, `bugfix`, `hotfix`, `patch`, `perf`, `performance`, `chore`
* **Skip (No bump):** `skip`, `chore-skip`

*(Note: `chore` and `chore-skip` are considered development-only changes).*

### Example

```text
feat(api): Add new authentication endpoint

This feature adds OAuth2 support to the core API.
It includes multiple lines in the description.
```

## Additional documentation

[Development documentation](README-DEV.md)

[Changelog](CHANGELOG.md)
