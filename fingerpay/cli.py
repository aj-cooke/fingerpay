from __future__ import annotations

import argparse
import getpass
import sys

from .core import FingerPayError, create_k, recover_card
from .session import FingerPaySession
from .storage import DEFAULT_K_PATH, load_k_token, save_k_token


def _read_k_from_args(args: argparse.Namespace) -> str:
    if args.k:
        return args.k.strip()
    if args.k_file:
        return load_k_token(args.k_file)
    return load_k_token()


def _cmd_create(args: argparse.Namespace) -> int:
    if args.stdout and args.out:
        raise FingerPayError("Use either --stdout or --out, not both")

    card = getpass.getpass("Card number (input hidden): ")
    pin = getpass.getpass("PIN: ")
    confirm = getpass.getpass("Confirm PIN: ")
    if pin != confirm:
        raise FingerPayError("PIN mismatch")
    if len(pin) < 4:
        raise FingerPayError("PIN must be at least 4 characters")

    token = create_k(card, pin, enforce_luhn=not args.no_luhn)

    if args.stdout:
        print(token)
    else:
        path = save_k_token(token, args.out)
        print(f"K written to {path}")

    card = ""
    pin = ""
    confirm = ""
    return 0


def _cmd_recover(args: argparse.Namespace) -> int:
    k_token = _read_k_from_args(args)
    pin = getpass.getpass("PIN: ")
    card = recover_card(k_token, pin)

    if args.mask_output:
        visible = card[-4:]
        print("Recovered card: " + "*" * (len(card) - 4) + visible)
    else:
        print("Recovered card:", card)

    pin = ""
    card = ""
    return 0


def _cmd_session_demo(args: argparse.Namespace) -> int:
    k_token = _read_k_from_args(args)
    pin = getpass.getpass("PIN: ")
    session = FingerPaySession(ttl_seconds=args.ttl_seconds)
    session.unlock(k_token, pin)

    card = session.get_card_for_autofill()
    if args.mask_output:
        print("Autofill card:", "*" * (len(card) - 4) + card[-4:])
    else:
        print("Autofill card:", card)

    session.lock()
    pin = ""
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FingerPay PIN-only prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-k", help="Create storable K token from C and P")
    create.add_argument(
        "--out",
        help=f"Write K token to a file (default: {DEFAULT_K_PATH})",
    )
    create.add_argument(
        "--stdout",
        action="store_true",
        help="Print K to stdout instead of storing to a file",
    )
    create.add_argument("--no-luhn", action="store_true", help="Skip Luhn validation")
    create.set_defaults(func=_cmd_create)

    recover = sub.add_parser("recover", help="Recover card C from K and PIN P")
    recover.add_argument("--k", help="K token directly")
    recover.add_argument(
        "--k-file",
        help=f"Read K token from file (default: {DEFAULT_K_PATH})",
    )
    recover.add_argument("--mask-output", action="store_true", help="Only show last 4 digits")
    recover.set_defaults(func=_cmd_recover)

    session_demo = sub.add_parser("session-demo", help="Demo in-memory unlock/get/lock API")
    session_demo.add_argument("--k", help="K token directly")
    session_demo.add_argument(
        "--k-file",
        help=f"Read K token from file (default: {DEFAULT_K_PATH})",
    )
    session_demo.add_argument("--ttl-seconds", type=int, default=None, help="Optional auto-lock TTL")
    session_demo.add_argument(
        "--mask-output", action="store_true", help="Only show last 4 digits"
    )
    session_demo.set_defaults(func=_cmd_session_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FingerPayError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
