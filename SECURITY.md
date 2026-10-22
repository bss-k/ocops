# Security

## Reporting a vulnerability

Please report security issues privately through GitHub's **Security → Report a vulnerability** form on this repository. Do not open a public issue. I'll acknowledge reports as soon as I can.

## Design

- **Keys never live in code.** API keys are read from environment variables (`.env`, which is git-ignored).
- **Least privilege.** Use one key per purpose, scoped to a single universe, with only the operations you need and an expiry date.
- **Writes are allowlisted.** DataStore writes and deletes are refused unless the DataStore name starts with `ocops_`.
- **Test profile by default.** `--profile prod` must be passed explicitly and requires typing `prod` to confirm each write.
- **Dry-run.** `--dry-run` shows old and new values without writing.
- **Audit log.** Every write records the old value in `audit.jsonl` (git-ignored, may contain player data), which `restore` uses to undo changes.
- **Protected users.** User IDs in `PROTECTED_USER_IDS` can never be banned.
- **Retries only for transient errors** (`429`, `5xx`, timeouts), with exponential backoff.

## Limits

- The `ocops_` guard is a client-side safety net, not a permission boundary: a key with write access can write to any DataStore in its universe. Scope keys tightly.
- `audit.jsonl` is local. Back it up if you rely on `restore`.
- No guarantee of being vulnerability-free. Use at your own risk and try commands on a throwaway universe first.
