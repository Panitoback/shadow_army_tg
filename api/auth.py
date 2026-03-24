import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException

from config import BOT_TOKEN


def validate_init_data(init_data: str) -> dict:
    """
    Validates Telegram WebApp initData using HMAC-SHA256.
    Returns the parsed user dict if valid, raises 401 otherwise.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    parsed = dict(parse_qsl(unquote(init_data), keep_blank_values=True))
    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in init data")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=BOT_TOKEN.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid init data")

    return json.loads(parsed.get("user", "{}"))
