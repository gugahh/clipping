"""
translate_news.py
-----------------
Translates English news text to Brazilian Portuguese using argostranslate 1.11.0.

First-time setup:  the script downloads the en → pt language package
automatically and caches it locally, so subsequent runs are fully offline.

Requirements:
    pip install argostranslate==1.11.0
"""

from argostranslate import package, translate


# ── Language pair ────────────────────────────────────────────────────────────
FROM_CODE = "en"
TO_CODE   = "pt"   # argostranslate uses "pt" for Portuguese (covers pt-BR)


def verifica_pacotes_linguagem() -> None:
    """Download the en→pt package the first time the script runs."""
    package.update_package_index()          # fetch the online package index
    available = package.get_available_packages()

    target = next(
        (p for p in available
         if p.from_code == FROM_CODE and p.to_code == TO_CODE),
        None,
    )

    if target is None:
        raise RuntimeError(
            f"No argostranslate package found for {FROM_CODE} → {TO_CODE}."
        )

    installed_codes = {
        (p.from_code, p.to_code)
        for p in package.get_installed_packages()
    }

    if (FROM_CODE, TO_CODE) not in installed_codes:
        print(f"Downloading language package ({FROM_CODE} → {TO_CODE})…")
        package.install_from_path(target.download())
        print("Package installed successfully.\n")
    else:
        print(f"Language package ({FROM_CODE} → {TO_CODE}) already installed.\n")


def translate_en_to_pt(text: str) -> str:
    """Translate *text* from English to Portuguese using the installed package."""
    installed = translate.get_installed_languages()

    src_lang = next((l for l in installed if l.code == FROM_CODE), None)
    tgt_lang = next((l for l in installed if l.code == TO_CODE),   None)

    if src_lang is None or tgt_lang is None:
        raise RuntimeError(
            "Required language not found among installed packages. "
            "Run verifica_pacotes_linguagem() first."
        )

    translation = src_lang.get_translation(tgt_lang)
    return translation.translate(text)


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    news_text = (
        "Over 180 people are feared dead or missing in the latest shipwrecks "
        "on the Mediterranean, according to the UN migration agency, IOM."
    )

    verifica_pacotes_linguagem()   # no-op after the first run

    print("Original (EN):")
    print(news_text)
    print()

    translated = translate_en_to_pt(news_text)

    print("Tradução (PT-BR):")
    print(translated)
