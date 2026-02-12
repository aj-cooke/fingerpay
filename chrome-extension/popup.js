const STORAGE_KEYS = {
  backendUrl: "backend_url",
  kToken: "k_token"
};

const els = {
  backendUrl: document.getElementById("backend-url"),
  createForm: document.getElementById("create-form"),
  card: document.getElementById("card"),
  createPin: document.getElementById("create-pin"),
  confirmPin: document.getElementById("confirm-pin"),
  recoverForm: document.getElementById("recover-form"),
  recoverPin: document.getElementById("recover-pin"),
  cardResult: document.getElementById("card-result"),
  cardValue: document.getElementById("card-value"),
  status: document.getElementById("status")
};

init().catch((err) => setStatus(err.message, true));

async function init() {
  const data = await chrome.storage.local.get([STORAGE_KEYS.backendUrl]);
  els.backendUrl.value = data[STORAGE_KEYS.backendUrl] || "http://127.0.0.1:8787";

  els.backendUrl.addEventListener("change", async () => {
    const url = els.backendUrl.value.trim();
    await chrome.storage.local.set({ [STORAGE_KEYS.backendUrl]: url });
    setStatus("Saved backend URL");
  });

  els.createForm.addEventListener("submit", onCreate);
  els.recoverForm.addEventListener("submit", onRecover);
}

async function onCreate(event) {
  event.preventDefault();
  clearStatus();

  const cardRaw = els.card.value.trim();
  const card = cardRaw.replace(/\D/g, "");
  const pin = els.createPin.value;
  const confirmPin = els.confirmPin.value;

  if (pin !== confirmPin) {
    setStatus("PIN mismatch", true);
    return;
  }
  if (pin.length < 4) {
    setStatus("PIN must be at least 4 characters", true);
    return;
  }
  if (!isLuhnValid(card)) {
    setStatus("Card number failed Luhn check", true);
    return;
  }

  try {
    const response = await callBackend("/create-k", { card, pin });
    if (!response.k_token) {
      throw new Error("Backend response missing k_token");
    }
    await chrome.storage.local.set({ [STORAGE_KEYS.kToken]: response.k_token });
    els.createForm.reset();
    setStatus("K generated and stored in extension storage");
  } catch (err) {
    setStatus(err.message, true);
  }
}

async function onRecover(event) {
  event.preventDefault();
  clearStatus();
  const action = event.submitter?.dataset?.action || "recover";

  const pin = els.recoverPin.value;
  if (pin.length < 4) {
    setStatus("PIN must be at least 4 characters", true);
    return;
  }

  const data = await chrome.storage.local.get([STORAGE_KEYS.kToken]);
  const kToken = data[STORAGE_KEYS.kToken];
  if (!kToken) {
    setStatus("No stored K token. Add a card first.", true);
    return;
  }

  try {
    const response = await callBackend("/recover-card", { k_token: kToken, pin });
    if (!response.card) {
      throw new Error("Backend response missing card");
    }

    if (action === "copy") {
      await copyText(response.card);
      els.recoverForm.reset();
      setStatus("Recovered card and copied to clipboard");
    } else {
      els.recoverForm.reset();
      setStatus("Recovered card (masked)");
    }

    const masked = maskCard(response.card);
    els.cardValue.textContent = masked;
    els.cardResult.hidden = false;
  } catch (err) {
    setStatus(err.message, true);
  }
}

async function callBackend(path, body) {
  const raw = (els.backendUrl.value || "").trim();
  if (!raw) {
    throw new Error("Set backend URL first");
  }

  let url;
  try {
    url = new URL(path, raw).toString();
  } catch {
    throw new Error("Invalid backend URL");
  }

  let res;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
  } catch {
    throw new Error("Could not reach backend. Is local API running?");
  }

  const data = await parseJsonSafe(res);
  if (!res.ok) {
    throw new Error(data.error || `Backend error (${res.status})`);
  }
  return data;
}

function parseJsonSafe(response) {
  return response
    .json()
    .catch(() => ({ error: "Backend returned non-JSON response" }));
}

function isLuhnValid(value) {
  if (!/^\d{12,19}$/.test(value)) {
    return false;
  }

  let sum = 0;
  const parity = value.length % 2;
  for (let i = 0; i < value.length; i += 1) {
    let digit = Number(value[i]);
    if (i % 2 === parity) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    sum += digit;
  }
  return sum % 10 === 0;
}

function maskCard(card) {
  const digits = String(card).replace(/\D/g, "");
  if (digits.length < 4) {
    return "****";
  }
  return `${"*".repeat(digits.length - 4)}${digits.slice(-4)}`;
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.className = isError ? "error" : "";
}

function clearStatus() {
  setStatus("");
}

async function copyText(value) {
  const text = String(value || "");
  if (!text) {
    throw new Error("Nothing to copy");
  }
  try {
    await navigator.clipboard.writeText(text);
    return;
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "absolute";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    if (!ok) {
      throw new Error("Clipboard write failed");
    }
  }
}
