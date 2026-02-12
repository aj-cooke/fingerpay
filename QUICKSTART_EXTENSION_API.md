# FingerPay Extension Quickstart

## Start The Local API

From the project root:

```bash
cd /home/ac/Documents/fingerpay
python3 -m fingerpay.api
```

Expected output:

- `FingerPay API listening on http://127.0.0.1:8787`
- `Endpoints: POST /create-k, POST /recover-card`

Keep this terminal running while using the extension.

## Load The Chrome Extension

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select folder: `/home/ac/Documents/fingerpay/chrome-extension`.
5. Click the extension icon and open **FingerPay Prototype**.
6. Confirm backend URL is `http://127.0.0.1:8787`.

## If You Change Extension Code

1. Go back to `chrome://extensions`.
2. Click **Reload** on FingerPay Prototype.
