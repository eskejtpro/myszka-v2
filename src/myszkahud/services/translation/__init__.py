"""Pakiet modułu tłumaczenia."""
from .translator import (
    TranslationService,
    SUPPORTED_LANGUAGES,
    build_translation_prompt,
    build_translation_system_instruction
)

__all__ = [
    "TranslationService",
    "SUPPORTED_LANGUAGES",
    "build_translation_prompt",
    "build_translation_system_instruction"
]
