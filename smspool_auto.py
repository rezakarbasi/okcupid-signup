"""
Two-function SMSPool helper for OkCupid:
  1) purchase_okcupid_number(...) -> returns phone_e164, phone_digits, phone_national, order_id, expires_in
  2) wait_for_sms(order_id, ...)  -> returns sms_code, full_message, messages(list), resend_available(bool)

Requires: requests
  pip install requests
"""

import os
import sys
import time
import signal
from typing import Any, Dict, Optional, List, Tuple

import requests

# ======================
# CONFIG (edit as needed)
# ======================
COUNTRY: str | int = "NL"   # ISO like "NL"/"GB"/"US" OR numeric id like 3/2/1
SERVICE_ID: int = 658       # OkCupid service id
API_KEY = os.getenv("SMSPOOL_API_KEY", "My-API-Key")

# If calling code is known, set it (digits only). If None, we try a small ISO->calling code map.
CALLING_CODE: Optional[str] = None  # e.g., "44" for UK, "31" for NL, "1" for US/CA

# Sensible waiting & resend policy
POLL_INTERVAL_SEC = 6
MAX_WAIT_SEC = 20 * 60
EXPIRE_GRACE_SEC = 4 * 60
AUTO_RESEND = True
RESEND_FIRST_AFTER = 90
RESEND_EVERY = 120
MAX_RESENDS = 2

API_BASE = "https://api.smspool.net"
UA = "okcupid-smspool-helper/3.1"

session = requests.Session()
session.headers.update({"User-Agent": UA})

# Minimal ISO -> calling code map (add more if you need)
COMMON_CALLING_CODES: Dict[str, str] = {
    "US": "1", "CA": "1", "GB": "44", "UK": "44",
    "NL": "31", "DE": "49", "FR": "33", "ES": "34", "IT": "39",
    "AU": "61", "NZ": "64", "SE": "46", "NO": "47", "DK": "45",
    "IE": "353", "CH": "41", "AT": "43", "BE": "32",
    "TR": "90", "PL": "48", "CZ": "420", "HU": "36",
    "IN": "91", "AE": "971", "SA": "966", "IR": "98",
}

# ------------------ HTTP helpers ------------------

def _post(path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not API_KEY or len(API_KEY) < 20:
        raise RuntimeError("Missing/invalid API key. Set SMSPOOL_API_KEY or edit API_KEY in the script.")
    payload = {"key": API_KEY, **data}
    r = session.post(f"{API_BASE}{path}", data=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    r = session.get(f"{API_BASE}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# ------------------ Informative (free) endpoints ------------------

def list_services(country: Optional[str | int] = None) -> List[Dict[str, Any]]:
    params = {"country": country} if country else None
    data = _get("/service/retrieve_all", params=params)
    return data if isinstance(data, list) else (data.get("data") or data.get("services") or [])

# ------------------ Paid endpoints ------------------

def purchase_number(service_id: int, country: str | int) -> Dict[str, Any]:
    return _post("/purchase/sms", {"service": service_id, "country": country})

def check_sms(order_id: str) -> Dict[str, Any]:
    return _post("/sms/check", {"orderid": order_id})

def check_resend(order_id: str) -> Dict[str, Any]:
    return _post("/sms/check_resend", {"orderid": order_id})

def resend(order_id: str) -> Dict[str, Any]:
    return _post("/sms/resend", {"orderid": order_id})

def cancel(order_id: str) -> Dict[str, Any]:
    return _post("/sms/cancel", {"orderid": order_id})

# ------------------ Helpers ------------------

def _digits(s: Any) -> str:
    """Return only digits from any input (int/str/None-safe)."""
    if s is None:
        return ""
    s_str = str(s)
    return "".join(ch for ch in s_str if ch.isdigit())

def _infer_calling_code(country: str | int) -> Optional[str]:
    if isinstance(country, int):
        return CALLING_CODE  # cannot infer from id alone
    iso = str(country).upper()
    return CALLING_CODE or COMMON_CALLING_CODES.get(iso)

def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default

def _extract_numbers_variants(raw_phone: Any, country: str | int) -> Tuple[str, str, str]:
    """
    Returns (phone_e164, phone_digits, phone_national_no_cc)
      phone_e164:   "+<digits>"
      phone_digits: "<digits>"  (no plus)
      phone_national_no_cc: digits with country code stripped if possible
    """
    d = _digits(raw_phone)  # now robust for int/str/None
    if not d:
        raise ValueError(f"Empty/invalid phone number: {raw_phone!r}")
    e164 = f"+{d}"
    cc = _infer_calling_code(country)
    if cc and d.startswith(cc):
        national = d[len(cc):]
    else:
        national = d
    return e164, d, national

def _service_listed_in_country(country: str | int, service_id: int) -> bool:
    try:
        svcs = list_services(country)
        for s in svcs:
            sid = _as_int(s.get("id") or s.get("ID") or s.get("service_id"))
            if sid == service_id:
                return True
        return False
    except Exception:
        return False

# =========================
# PUBLIC: two main functions
# =========================

def purchase_okcupid_number(
    country: str | int,
    service_id: int,
    api_key: Optional[str] = None,
    calling_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Order a number for the given country/service.
    Returns:
      {
        "phone_e164": "+<digits>",
        "phone_digits": "<digits>",
        "phone_national": "<digits-without-country-code>",
        "order_id": "<id>",
        "expires_in": <seconds>,
      }
    """
    global API_KEY, CALLING_CODE
    if api_key:
        API_KEY = api_key
    if calling_code:
        CALLING_CODE = str(calling_code)

    # Free guard: avoid paid failure if service isn't listed right now
    if not _service_listed_in_country(country, service_id):
        raise RuntimeError(f"Service {service_id} is not listed for country={country!r} right now.")

    order = purchase_number(service_id, country)
    if not order or not order.get("success"):
        raise RuntimeError(f"Order failed: {order}")

    # number can be int or str -> coerce to str safely
    phone_raw = order.get("number") or order.get("phonenumber")
    phone_e164, phone_digits, phone_national = _extract_numbers_variants(phone_raw, country)

    return {
        "phone_e164": phone_e164,
        "phone_digits": phone_digits,
        "phone_national": phone_national,
        "order_id": order.get("order_id") or order.get("orderid") or order.get("order_code"),
        "expires_in": _as_int(order.get("expires_in"), 600),
    }

def wait_for_sms(
    order_id: str,
    api_key: Optional[str] = None,
    poll_interval_sec: int = POLL_INTERVAL_SEC,
    max_wait_sec: int = MAX_WAIT_SEC,
    expire_grace_sec: int = EXPIRE_GRACE_SEC,   # currently unused but kept for API compat
    auto_resend: bool = AUTO_RESEND,
    first_resend_after: int = RESEND_FIRST_AFTER,
    resend_every: int = RESEND_EVERY,
    max_resends: int = MAX_RESENDS,
) -> Dict[str, Any]:
    """
    Poll until SMS arrives or timeout.
    Returns:
      {
        "sms_code": "<code or None>",
        "full_message": "<text or ''>",
        "messages": [list of unique full messages],
        "resend_available": True/False
      }
    """
    if api_key:
        global API_KEY
        API_KEY = api_key

    hard_deadline = time.time() + max_wait_sec
    last_status = None
    received_messages: List[str] = []
    resend_count = 0
    next_resend_at = time.time() + first_resend_after if auto_resend else float("inf")

    def on_sigint(signum, frame):
        print("\nCtrl+C detected. Cancelling order…")
        try:
            resp = cancel(order_id)
            print(f"Cancel response: {resp}")
        finally:
            sys.exit(130)

    signal.signal(signal.SIGINT, on_sigint)

    while time.time() < hard_deadline:
        # Limited resend policy
        if auto_resend and resend_count < max_resends and time.time() >= next_resend_at:
            try:
                cr = check_resend(order_id)
                can = int(str(cr.get("can_resend", cr.get("resend", 0)) or "0"))
                if can:
                    rr = resend(order_id)
                    resend_count += 1
                    print(f"[resend] requested (count={resend_count}) → {rr}")
                else:
                    print("[resend] not available yet/anymore.")
            except Exception as e:
                print(f"[resend] check/request failed: {e}")
            next_resend_at = time.time() + resend_every

        # Check SMS
        try:
            ck = check_sms(order_id)
        except requests.HTTPError as e:
            print(f"[check] HTTP {e.response.status_code}: {e.response.text.strip()[:200]}")
            time.sleep(poll_interval_sec)
            continue
        except Exception as e:
            print(f"[check] error: {e}")
            time.sleep(poll_interval_sec)
            continue

        status = ck.get("status")
        sms_code = ck.get("sms") or ck.get("code")
        full_sms = ck.get("full_sms") or ck.get("sms_message") or ""

        if status != last_status:
            print(f"Status: {status} {'… waiting' if not sms_code else '… code received'}")
            last_status = status

        if full_sms and full_sms not in received_messages:
            received_messages.append(full_sms)

        if sms_code or full_sms:
            resend_avail = False
            try:
                cr = check_resend(order_id)
                resend_avail = bool(int(str(cr.get("can_resend", cr.get("resend", 0)) or "0")))
            except Exception:
                pass

            return {
                "sms_code": sms_code,
                "full_message": full_sms,
                "messages": received_messages,
                "resend_available": resend_avail,
            }

        time.sleep(poll_interval_sec)

    # Timeout: best-effort cancel
    try:
        cancel(order_id)
    except Exception:
        pass
    return {"sms_code": None, "full_message": "", "messages": received_messages, "resend_available": False}

# ======================
# Demo: one-shot workflow
# ======================
if __name__ == "__main__":
    info = purchase_okcupid_number(COUNTRY, SERVICE_ID)
    print("\n=== NUMBER ACQUIRED ===")
    print(f"Full (E.164):         {info['phone_e164']}")
    print(f"Digits only:          {info['phone_digits']}")
    print(f"National (no CC):     {info['phone_national']}")
    print(f"Order ID:             {info['order_id']}")
    print(f"Expires in (seconds): {info['expires_in']}\n")

    print("Trigger the OkCupid SMS to the number above, then waiting…\n")

    result = wait_for_sms(info["order_id"])
    print("\n=== RESULT ===")
    print(f"Code:          {result['sms_code']}")
    print(f"Full message:  {result['full_message']}")
    if len(result["messages"]) > 1:
        print(f"Multiple messages received: {len(result['messages'])}")
    print(f"Resend available now: {result['resend_available']}")
