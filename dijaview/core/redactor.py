import re
from typing import List, Optional, Tuple

REDACTION_PATTERNS = [
    # Authorization header tokens
    (r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9_\-\.]{8,}", r"\1[REDACTED_TOKEN]"),
    (r"(?i)(bearer\s+)[A-Za-z0-9_\-\.]{12,}", r"\1[REDACTED_TOKEN]"),
    (r"(?i)(authorization:\s*basic\s+)[A-Za-z0-9+/=]{10,}", r"\1[REDACTED_BASIC_AUTH]"),

    # Common provider API keys
    (r"gh[pousr]_[A-Za-z0-9_]{36,}", "[REDACTED_GITHUB_KEY]"),
    (r"sk-(?:live|test)?[A-Za-z0-9_\-]{20,}", "[REDACTED_API_KEY]"),
    (r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),

    # Generic token and secret assignment in env / flags
    (r"(?i)(api[_-]?key\s*[=:]\s*['\"]?)[A-Za-z0-9_\-\.]{8,}['\"]?", r"\1[REDACTED_KEY]"),
    (r"(?i)(secret[_-]?key\s*[=:]\s*['\"]?)[A-Za-z0-9_\-\.]{8,}['\"]?", r"\1[REDACTED_SECRET]"),
    (r"(?i)(password\s*[=:]\s*['\"]?)[^\s'\"]{4,}['\"]?", r"\1[REDACTED_PASSWORD]"),
    (r"(?i)(--password\s+)[^\s]{4,}", r"\1[REDACTED_PASSWORD]"),
    (r"(?i)(--token\s+)[^\s]{8,}", r"\1[REDACTED_TOKEN]"),
    (r"(?i)(--api-key\s+)[^\s]{8,}", r"\1[REDACTED_API_KEY]"),

    # Database connection URIs
    (r"(?i)([a-z0-9+]+://[^:]+:)([^@]+)(@)", r"\1[REDACTED_PASSWORD]\3"),

    # Private Key blocks
    (r"-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----[\s\S]*?-----END[ A-Z0-9_-]+PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
]


def redact_secrets(text: str, custom_rules: Optional[List[Tuple[str, str]]] = None) -> str:
    """Masks credentials, API keys, passwords, tokens, and custom filters in input text."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)
    if custom_rules:
        for pattern, replacement in custom_rules:
            try:
                sanitized = re.sub(pattern, replacement, sanitized)
            except Exception:
                continue
    return sanitized
