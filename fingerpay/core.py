from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets

VERSION = 1
SCRYPT_N = 1 << 14
SCRYPT_R = 8
SCRYPT_P = 1


class FingerPayError(Exception):
    pass


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _b64d(text: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(text.encode("ascii"))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise FingerPayError("Invalid base64 in K") from exc


def _scrypt(pin: str, salt: bytes, length: int) -> bytes:
    return hashlib.scrypt(
        pin.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=length,
    )


def _normalize_card(card: str) -> str:
    digits = "".join(ch for ch in card if ch.isdigit())
    if not (12 <= len(digits) <= 19):
        raise FingerPayError("Card number must be 12-19 digits")
    return digits


def _luhn_ok(number: str) -> bool:
    total = 0
    parity = len(number) % 2
    for idx, ch in enumerate(number):
        digit = int(ch)
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _build_mask(card: str, stream: bytes) -> str:
    masked = []
    for i, ch in enumerate(card):
        c = int(ch)
        s = stream[i] % 10
        masked.append(str((c - s) % 10))
    return "".join(masked)


def _recover_from_mask(masked: str, stream: bytes) -> str:
    digits = []
    for i, ch in enumerate(masked):
        k = int(ch)
        s = stream[i] % 10
        digits.append(str((k + s) % 10))
    return "".join(digits)


def _derive_material(pin: str, salt: bytes, nonce: bytes, card_len: int) -> tuple[bytes, bytes]:
    # Domain separation so masking stream and tag key are independent.
    mask_stream = _scrypt(pin, salt + nonce + b"|mask", card_len)
    tag_key = _scrypt(pin, salt + nonce + b"|tag", 32)
    return mask_stream, tag_key


def _tag_card(card: str, tag_key: bytes) -> str:
    return hashlib.blake2s(card.encode("ascii"), key=tag_key, digest_size=16).hexdigest()


def create_k(card: str, pin: str, enforce_luhn: bool = True) -> str:
    card_digits = _normalize_card(card)
    if enforce_luhn and not _luhn_ok(card_digits):
        raise FingerPayError("Card number failed Luhn check")

    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(16)
    stream, tag_key = _derive_material(pin, salt, nonce, len(card_digits))

    payload = {
        "v": VERSION,
        "alg": "digit-mask-scrypt-v1",
        "n": SCRYPT_N,
        "r": SCRYPT_R,
        "p": SCRYPT_P,
        "len": len(card_digits),
        "salt": _b64e(salt),
        "nonce": _b64e(nonce),
        "mask": _build_mask(card_digits, stream),
        "tag": _tag_card(card_digits, tag_key),
    }
    token = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    # Best-effort memory hygiene.
    stream = b""
    tag_key = b""
    card_digits = ""
    return token


def recover_card(k_token: str, pin: str) -> str:
    try:
        payload = json.loads(_b64d(k_token).decode("utf-8"))
    except Exception as exc:
        raise FingerPayError("Malformed K token") from exc

    if payload.get("v") != VERSION or payload.get("alg") != "digit-mask-scrypt-v1":
        raise FingerPayError("Unsupported K format")

    for field in ("salt", "nonce", "mask", "tag", "len"):
        if field not in payload:
            raise FingerPayError(f"K missing field: {field}")

    mask = payload["mask"]
    if not isinstance(mask, str) or not mask.isdigit() or len(mask) != int(payload["len"]):
        raise FingerPayError("Invalid mask in K")

    salt = _b64d(payload["salt"])
    nonce = _b64d(payload["nonce"])

    stream, tag_key = _derive_material(pin, salt, nonce, len(mask))
    card = _recover_from_mask(mask, stream)
    expected = _tag_card(card, tag_key)

    if not hmac.compare_digest(expected, payload["tag"]):
        raise FingerPayError("Invalid PIN or corrupted K")

    stream = b""
    tag_key = b""
    return card
