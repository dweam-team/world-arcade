import base64
import hashlib
import hmac
from time import time


def create_turn_credentials(turn_secret_key: str, expiration: int = 24*3600) -> dict:
    """
    Create TURN credentials using a secret key and expiration time.
    """
    timestamp = int(time()) + expiration
    username = str(timestamp)
    key = bytes(turn_secret_key, 'utf-8')
    message = bytes(username, 'utf-8')
    dig = hmac.new(key, message, hashlib.sha1).digest()
    password = base64.b64encode(dig).decode()
    return {
        "username": username,
        "credential": password,
        "ttl": expiration
    }
