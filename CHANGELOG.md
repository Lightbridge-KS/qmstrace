# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- The package skeleton: a `qmstrace` command with `--version` and plain-text help.
- Exit codes as a contract: `0` no failing findings, `1` the check failed, `2` could not judge,
  `3` internal error — never a bare traceback.
- The dry gate (`just dry`) and a pipeline that runs it: format, lint, types, tests with a
  coverage floor, and a check that the built wheel carries the package data.
- A test that enforces the import matrix between the package's layers.
