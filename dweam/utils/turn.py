import base64
import hashlib
import hmac
from time import time
import os
from fastapi import Request


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


def get_turn_stun_urls(turn_base_url: str | None = None) -> tuple[str, str]:
    """Get TURN and STUN URLs from environment or request
    
    Args:
        turn_base_url: Base URL for the TURN server
        
    Returns:
        Tuple of (turn_url, stun_url)
    """
    if turn_base_url is None:
        turn_base_url = os.environ.get('INTERNAL_TURN_URL', "localhost:3478")
        
    return (f"turn:{turn_base_url}", f"stun:{turn_base_url}")
