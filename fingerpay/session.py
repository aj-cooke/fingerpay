from __future__ import annotations

import time

from .core import FingerPayError, recover_card


class FingerPaySession:
    """In-memory only unlock session for extension-style flows."""

    def __init__(self, ttl_seconds: int | None = None) -> None:
        self._card_number: str | None = None
        self._unlocked_at: float | None = None
        self._ttl_seconds = ttl_seconds

    def unlock(self, k_token: str, pin: str) -> None:
        self._card_number = recover_card(k_token, pin)
        self._unlocked_at = time.monotonic()

    def get_card_for_autofill(self) -> str:
        if self._card_number is None:
            raise FingerPayError("Session is locked")
        if self._is_expired():
            self.lock()
            raise FingerPayError("Session expired")
        return self._card_number

    def lock(self) -> None:
        self._card_number = None
        self._unlocked_at = None

    def is_unlocked(self) -> bool:
        if self._card_number is None:
            return False
        if self._is_expired():
            self.lock()
            return False
        return True

    def _is_expired(self) -> bool:
        if self._ttl_seconds is None or self._unlocked_at is None:
            return False
        return (time.monotonic() - self._unlocked_at) >= self._ttl_seconds
