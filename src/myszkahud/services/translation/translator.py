"""Moduł domenowy tłumaczenia tekstu (MyszkaHUD 0.3)."""

from typing import Optional, Dict
from myszkahud.services.gemini.client import AITextProvider


SUPPORTED_LANGUAGES: Dict[str, str] = {
    "pl": "Polski",
    "en": "Angielski",
    "de": "Niemiecki",
    "es": "Hiszpański",
    "fr": "Francuski",
    "uk": "Ukraiński",
    "it": "Włoski",
    "auto": "Automatyczny",
}


def build_translation_system_instruction() -> str:
    """Instrukcja systemowa zapewniająca czyste i naturalne tłumaczenie bez dopowiedzeń."""
    return (
        "Jesteś profesjonalnym, precyzyjnym tłumaczem tekstu. "
        "Twoim zadaniem jest wyłącznie przetłumaczenie podanego tekstu na język docelowy. "
        "ZASADY BEZWZGLĘDNE:\n"
        "1. Zwróć WYŁĄCZNIE przetłumaczony tekst. Nie dodawaj żadnych komentarzy, wyjaśnień ani znaczników Markdown (chyba że występowały w oryginale).\n"
        "2. Zachowaj oryginalne formatowanie, znaki nowej linii, wcięcia i interpunkcję.\n"
        "3. Tłumacz naturalnie i kontekstowo, z zachowaniem terminologii branżowej lub potocznej adekwatnie do źródła."
    )


def build_translation_prompt(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """Buduje prompt dla silnika AI."""
    src_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
    tgt_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)

    if source_lang == "auto":
        return f"Przetłumacz poniższy tekst na język docelowy ({tgt_name}):\n\n{text}"
    else:
        return f"Przetłumacz poniższy tekst z języka {src_name} na język {tgt_name}:\n\n{text}"


class TranslationService:
    """
    Warstwa domenowa tłumacza.
    Zależy wyłącznie od interfejsu AITextProvider (np. GeminiService).
    """

    def __init__(self, ai_provider: AITextProvider):
        self.ai_provider = ai_provider

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en"
    ) -> str:
        """
        Waliduje wejście, buduje prompt i deleguje wykonanie do dostawcy AI.
        """
        if not text or not text.strip():
            return ""

        clean_text = text.strip()
        system_instruction = build_translation_system_instruction()
        prompt = build_translation_prompt(clean_text, source_lang=source_lang, target_lang=target_lang)

        translated = self.ai_provider.generate_text(prompt, system_instruction=system_instruction)
        return translated.strip()
