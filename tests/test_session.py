import pytest

from fingerpay import FingerPayError, FingerPaySession, create_k


def test_session_lock_clears_card() -> None:
    k = create_k("4242424242424242", "1234")
    session = FingerPaySession()

    session.unlock(k, "1234")
    assert session.is_unlocked() is True
    assert session.get_card_for_autofill() == "4242424242424242"

    session.lock()
    assert session.is_unlocked() is False
    with pytest.raises(FingerPayError, match="Session is locked"):
        session.get_card_for_autofill()


def test_session_ttl_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    k = create_k("4242424242424242", "1234")
    current = {"t": 100.0}

    def fake_monotonic() -> float:
        return current["t"]

    monkeypatch.setattr("fingerpay.session.time.monotonic", fake_monotonic)

    session = FingerPaySession(ttl_seconds=5)
    session.unlock(k, "1234")
    assert session.is_unlocked() is True

    current["t"] = 106.0
    assert session.is_unlocked() is False
    with pytest.raises(FingerPayError, match="Session is locked"):
        session.get_card_for_autofill()
