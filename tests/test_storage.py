from pathlib import Path

import pytest

from fingerpay import FingerPayError
from fingerpay.storage import load_k_token, save_k_token


def test_save_and_load_k_token(tmp_path: Path) -> None:
    target = tmp_path / "k.token"
    save_k_token("abc123", str(target))
    assert load_k_token(str(target)) == "abc123"


def test_load_missing_k_token_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.token"
    with pytest.raises(FingerPayError, match="K file not found"):
        load_k_token(str(missing))
