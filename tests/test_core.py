import pytest

from fingerpay import FingerPayError, create_k, recover_card


def test_create_and_recover_roundtrip() -> None:
    k = create_k("4242 4242 4242 4242", "1234")
    assert recover_card(k, "1234") == "4242424242424242"


def test_wrong_pin_fails() -> None:
    k = create_k("4242424242424242", "1234")
    with pytest.raises(FingerPayError, match="Invalid PIN"):
        recover_card(k, "9999")
