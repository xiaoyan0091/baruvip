import hashlib
import hmac
import os
from urllib.parse import parse_qsl

BOT_TOKEN = os.getenv("BOT_TOKEN")

def is_valid_init_data(init_data: str, bot_token: str) -> bool:
    """
    Validates the initData string from a Telegram Mini App.
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        hash_from_telegram = parsed_data.pop('hash')

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        return calculated_hash == hash_from_telegram
    except (KeyError, TypeError, ValueError):
        return False
