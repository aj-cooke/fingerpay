from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .core import FingerPayError, create_k, recover_card


class FingerPayAPIHandler(BaseHTTPRequestHandler):
    server_version = "FingerPayAPI/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(204, {})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/create-k":
            self._handle_create_k()
            return
        if self.path == "/recover-card":
            self._handle_recover_card()
            return
        self._send_error_json(404, "Not found")

    def _handle_create_k(self) -> None:
        body = self._read_json_body()
        if body is None:
            return

        card = str(body.get("card", "")).strip()
        pin = str(body.get("pin", ""))
        if len(pin) < 4:
            self._send_error_json(400, "PIN must be at least 4 characters")
            return

        try:
            k_token = create_k(card, pin, enforce_luhn=True)
        except FingerPayError as exc:
            self._send_error_json(400, str(exc))
            return

        self._send_json(200, {"k_token": k_token})

    def _handle_recover_card(self) -> None:
        body = self._read_json_body()
        if body is None:
            return

        k_token = str(body.get("k_token", "")).strip()
        pin = str(body.get("pin", ""))
        if not k_token:
            self._send_error_json(400, "k_token is required")
            return
        if len(pin) < 4:
            self._send_error_json(400, "PIN must be at least 4 characters")
            return

        try:
            card = recover_card(k_token, pin)
        except FingerPayError as exc:
            self._send_error_json(400, str(exc))
            return

        self._send_json(200, {"card": card})

    def _read_json_body(self) -> dict[str, Any] | None:
        content_length = self.headers.get("Content-Length")
        content_type = self.headers.get("Content-Type", "")

        if not content_length:
            self._send_error_json(400, "Request body is required")
            return None
        if "application/json" not in content_type.lower():
            self._send_error_json(415, "Content-Type must be application/json")
            return None

        try:
            raw = self.rfile.read(int(content_length))
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_error_json(400, "Malformed JSON body")
            return None

        if not isinstance(body, dict):
            self._send_error_json(400, "JSON body must be an object")
            return None

        return body

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        if status_code != 204:
            self.wfile.write(data)

    def _send_error_json(self, status_code: int, message: str) -> None:
        self._send_json(status_code, {"error": message})

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), FingerPayAPIHandler)
    print(f"FingerPay API listening on http://{host}:{port}")
    print("Endpoints: POST /create-k, POST /recover-card")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FingerPay local API for extension integration")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8787, help="Bind port (default: 8787)")
    args = parser.parse_args(argv)

    run_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
