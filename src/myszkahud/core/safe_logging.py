"""Moduł bezpiecznego logowania z automatyczną sanityzacją danych wrażliwych."""

import re
import logging
from typing import Any

# Wzorce wykrywania potencjalnych kluczy API, tokenów i haseł
SENSITIVE_PATTERNS = [
    (re.compile(r'AIza[0-9A-Za-z_\-]{25,45}'), '[GEMINI_API_KEY_REDACTED]'),
    (re.compile(r'sk-[a-zA-Z0-9_\-]{20,}'), '[API_KEY_REDACTED]'),
    (re.compile(r'bearer\s+[a-zA-Z0-9_\-\.]+', re.IGNORECASE), 'Bearer [TOKEN_REDACTED]'),
]


def sanitize_text(text: str) -> str:
    """Usuwa potencjalne klucze API i tokeny z tekstu logów."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class SensitiveDataFilter(logging.Filter):
    """Filtr logowania Pythona usuwający klucze i wrażliwe dane z komunikatów."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: sanitize_text(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(sanitize_text(str(a)) for a in record.args)
        return True


def setup_safe_logging(level: int = logging.INFO) -> None:
    """Konfiguruje globalny root logger z filtrem danych wrażliwych."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger("myszkahud")
    root_logger.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
