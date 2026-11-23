# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
While the version is `0.x`, minor releases may contain breaking changes.

## [Unreleased]

## [0.1.0] - 2026-11-23

First release.

### Added

- DataStores: `datastores`, `keys` and `get` to inspect, with cursor pagination across all pages.
- Safe writes: `set`, `delete` and `restore`, all routed through one shared change path.
  - Only DataStores starting with `ocops_` can be changed (override with `OCOPS_SAFE_PREFIX`).
  - `--dry-run` on every write, showing old vs new.
  - An append-only audit log (`audit.jsonl`) records the previous value, so `restore` can undo the last change.
- Profiles: `test` by default; `prod` requires typing a confirmation word.
- Moderation through the User Restrictions API: `ban` (permanent or `--hours`), `unban`, and `bans`.
  Protected user IDs can't be banned.
- Retries with exponential backoff and a capped delay, for transient errors (429 and 5xx) only.
- Packaging: `pip install .` provides the `ocops` command (Python 3.10+).
- Tests: 14 pytest tests with a mocked HTTP layer, so no real keys or universes are touched.
- CI: tests on Python 3.10 and 3.13, plus a gitleaks secret scan.

### Fixed (before release)

- `ban --hours 0` no longer turns into a permanent ban: hours must be greater than 0.
- `set` refuses a `null` value instead of silently deleting the entry; use `delete` for that.
- `set` with invalid JSON exits with a clear message instead of crashing.

[Unreleased]: https://github.com/bss-k/ocops/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bss-k/ocops/releases/tag/v0.1.0
