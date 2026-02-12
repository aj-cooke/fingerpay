import json
import threading
import urllib.error
import urllib.request

import pytest

from fingerpay.api import FingerPayAPIHandler, ThreadingHTTPServer


def _post_json(base_url: str, path: str, payload: dict[str, str]) -> tuple[int, dict[str, str]]:
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), body
    except urllib.error.HTTPError as err:
        body = json.loads(err.read().decode("utf-8"))
        return int(err.code), body


@pytest.fixture
def api_server() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FingerPayAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    host, port = server.server_address
    base_url = f"http://{host}:{port}"

    yield base_url

    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_create_and_recover_card(api_server: str) -> None:
    status, created = _post_json(
        api_server,
        "/create-k",
        {"card": "4242424242424242", "pin": "1234"},
    )
    assert status == 200
    assert "k_token" in created

    status, recovered = _post_json(
        api_server,
        "/recover-card",
        {"k_token": created["k_token"], "pin": "1234"},
    )
    assert status == 200
    assert recovered["card"] == "4242424242424242"


def test_recover_wrong_pin_returns_400(api_server: str) -> None:
    status, created = _post_json(
        api_server,
        "/create-k",
        {"card": "4242424242424242", "pin": "1234"},
    )
    assert status == 200

    status, recovered = _post_json(
        api_server,
        "/recover-card",
        {"k_token": created["k_token"], "pin": "9999"},
    )
    assert status == 400
    assert "Invalid PIN" in recovered["error"]
