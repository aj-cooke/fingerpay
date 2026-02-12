#!/usr/bin/env python3

from __future__ import annotations

import getpass

from fingerpay import FingerPayError, create_k, recover_card
from fingerpay.storage import DEFAULT_K_PATH, load_k_token, save_k_token


def _print_menu() -> None:
    print("Choose an action:")
    print("1. Provide PIN to print card number (C)")
    print("2. Add a new card (enter C and P)")


def _handle_recover() -> int:
    k_token = load_k_token()
    pin = getpass.getpass("PIN (P): ")
    card = recover_card(k_token, pin)
    print(f"Card number (C): {card}")
    pin = ""
    card = ""
    return 0


def _handle_add_card() -> int:
    card = getpass.getpass("Card number (C): ")
    pin = getpass.getpass("PIN (P): ")
    confirm = getpass.getpass("Confirm PIN (P): ")
    if pin != confirm:
        raise FingerPayError("PIN mismatch")
    if len(pin) < 4:
        raise FingerPayError("PIN must be at least 4 characters")

    k_token = create_k(card, pin, enforce_luhn=True)
    path = save_k_token(k_token)
    print(f"K stored at {path}")

    card = ""
    pin = ""
    confirm = ""
    return 0


def main() -> int:
    try:
        _print_menu()
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return _handle_recover()
        if choice == "2":
            return _handle_add_card()
        raise FingerPayError("Invalid selection. Choose 1 or 2.")
    except FingerPayError as exc:
        print(f"Error: {exc}")
        print(f"Expected K storage path: {DEFAULT_K_PATH}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
