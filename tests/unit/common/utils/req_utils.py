from app import CSRF_HEADER_NAME


def make_csrf_token_header(csrf_token: str) -> dict[str, str]:
    """Generates the CSRF header for inclusion in unsafe requests, given the token"""

    return {CSRF_HEADER_NAME: csrf_token}
