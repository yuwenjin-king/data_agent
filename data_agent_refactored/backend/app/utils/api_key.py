import secrets
import string

API_KEY_PREFIX = "sk-"
API_KEY_RANDOM_LENGTH = 32


def generate_api_key() -> str:
    """Generate a secure API key in the form sk-<32 alphanumerics>."""
    random_part = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(API_KEY_RANDOM_LENGTH)
    )
    return f"{API_KEY_PREFIX}{random_part}"


def mask_api_key(key: str | None) -> str | None:
    """Return a masked representation of an API key, e.g. '****abcd'."""
    if not key:
        return None
    if len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"
