# FingerPay Session Summary

## Project Goal (Current Scope)
Build a PIN-only prototype where:
- `K` is stored.
- `P` (PIN) is never persisted.
- `C` (card number) is never persisted in plaintext.
- Runtime recovery uses `f(K, P) = C`.

Fingerprint and Chrome extension work are intentionally deferred.

## Current State
A working Python prototype exists with:
- Core K generation/recovery logic.
- In-memory unlock session API.
- K file storage helpers.
- One interactive launcher flow (`run.py`) with two options:
  1. Enter PIN to print card number.
  2. Add new card by entering card number + PIN (generates/stores K).

## Code Layout
- `fingerpay/core.py`
- `fingerpay/session.py`
- `fingerpay/storage.py`
- `fingerpay/cli.py`
- `fingerpay/__init__.py`
- `run.py`
- `tests/test_core.py`
- `tests/test_session.py`
- `tests/test_storage.py`
- `README`

## How It Works
- `create_k(card, pin)` in `fingerpay/core.py` creates a token `K`.
- `recover_card(k, pin)` in `fingerpay/core.py` reconstructs `C` from `K + P`.
- `FingerPaySession` in `fingerpay/session.py` supports:
  - `unlock(k, pin)`
  - `get_card_for_autofill()`
  - `lock()`
  - optional TTL auto-lock
- `save_k_token`/`load_k_token` in `fingerpay/storage.py` handle persistence.

## Interactive Entry Point
Run:
```bash
python3 run.py
```
Menu:
- `1`: Ask for PIN and print recovered card number from stored `K`.
- `2`: Ask for card number + PIN, generate/store new `K`.

Default `K` path:
- `~/.fingerpay/k.token`

## Advanced CLI (Still Available)
```bash
python3 -m fingerpay.cli --help
```
Supports subcommands (`create-k`, `recover`, `session-demo`) and custom K input/output flags.

## Security Notes / Constraints
- Only `K` is stored by design.
- PIN is prompted at runtime and not written to files.
- Card is reconstructed in process memory during use.
- Important caveat: if `f(K, P) = C`, then `K` is still a reversible protected representation of card data (cryptographically equivalent in effect to encrypted form).

## Testing Status
- `pytest` tests are authored under `tests/`.
- In this environment, `pytest` is not installed (`python3 -m pytest` fails).
- Smoke tests were run via inline `python3` snippets and passed.

## Repo Status (At Handoff)
There are local uncommitted changes/new files, including:
- `README` modified
- `fingerpay/` added
- `run.py` added
- `tests/` added
- `SESSION_SUMMARY.md` added

## Suggested Next Steps
1. Install test tooling (`pytest`) and run full test suite.
2. Add input/output masking policy (possibly mask by default when printing `C`).
3. Add lockout/rate-limit for repeated wrong PIN attempts.
4. Define extension-facing API contract for future Chrome integration.
5. Decide how long unlocked data may remain in memory (TTL defaults/policy).

## Quick Resume Checklist
1. `cd /home/ac/Documents/fingerpay`
2. Run `python3 run.py`
3. If needed, inspect advanced commands with `python3 -m fingerpay.cli --help`
4. If adding tests, install `pytest` then run `python3 -m pytest -q`
