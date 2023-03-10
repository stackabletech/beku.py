# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

- Install and run pylint and mypy.
- Reorganize package modules.
- Install GitHub linting actions.
- Install pre-commit hooks.

## [0.0.5] - 2023-01-23

### Changed

- Preserve file permissions for the generated files.

## [0.0.4] - 2023-01-20

### Changed

- Prevent the `lookup()` function from raising an exception.

## [0.0.3] - 2023-01-20

### Changed

- Add `lookup()` function for (partial) compatibility with Ansible templates.

## [0.0.2] - 2023-01-20

### Changed

- Enable `trim_blocks` when processing Jinja templates to avoid spurious new lines. These can lead to broken shell commands.

## [0.0.1] - 2022-12-20

### Added

- Initial release.
