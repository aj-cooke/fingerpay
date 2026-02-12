# FingerPay Encryption/Decryption Model

## What It Is

This project does not use standard card encryption at rest. It stores a reversible token `K` built from:
- card digits `C`
- PIN `P`
- random `salt` + `nonce`
- scrypt-derived material

Core logic is in `fingerpay/core.py`.

## Create (`C + P -> K`)

From `fingerpay/core.py`:

1. Normalize/validate card in `_normalize_card` and `_luhn_ok`.
2. Generate random `salt` (16 bytes) and `nonce` (16 bytes).
3. Derive two PIN-dependent values with scrypt (`_derive_material`):
   - `mask_stream` for digit masking
   - `tag_key` for integrity/auth check
4. Build masked digits with `_build_mask`:
   - each card digit is shifted mod 10 by `mask_stream[i] % 10`
5. Compute keyed integrity tag with `_tag_card` (BLAKE2s keyed hash of recovered card).
6. Store payload fields (`v`, `alg`, scrypt params, `len`, `salt`, `nonce`, `mask`, `tag`) as JSON, then base64url encode => this is `K`.

Main entry: `create_k` in `fingerpay/core.py`.

## Recover (`K + P -> C`)

Also in `fingerpay/core.py`:

1. Base64 decode + parse payload from `K`.
2. Validate format/version/required fields.
3. Re-derive `mask_stream` and `tag_key` from `P`, `salt`, `nonce`.
4. Reconstruct card digits with `_recover_from_mask` (inverse mod-10 shift).
5. Recompute tag and compare with stored tag using constant-time compare (`hmac.compare_digest`).
6. If tag matches, return card. Otherwise: `Invalid PIN or corrupted K`.

Main entry: `recover_card` in `fingerpay/core.py`.

## Important Security Properties

1. `P` is never persisted by design (runtime input only).
2. Plain card is not stored on disk; only `K` is.
3. Wrong PIN cannot silently return garbage because tag verification fails.
4. Salt+nonce randomness means different `K` each time, even for same `C` and `P`.

## Critical Caveat

`K` is still a reversible protected representation of the card, not one-way tokenization.
If an attacker gets `K`, they can brute-force `P` offline (scrypt slows this, but does not prevent weak-PIN attacks).
So practical security mostly depends on PIN strength + rate limiting at app layer.

## Current Parameters

From `fingerpay/core.py`:
- `SCRYPT_N = 2^14`, `r = 8`, `p = 1`
- BLAKE2s keyed tag, 16-byte digest
- Card length allowed: 12-19 digits
- Luhn enforced in `run.py` add-card flow

## What This Means Operationally

1. Treat `K` as sensitive secret (similar handling to encrypted card blob).
2. Enforce stronger PIN policy if you want real protection.
3. Add lockout/rate limiting for repeated failed PIN attempts.
4. Keep unlocked card in memory for minimal time (TTL/lock behavior in `fingerpay/session.py`).
