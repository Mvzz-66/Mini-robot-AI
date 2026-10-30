"""
Caricamento delle impostazioni da config.json.

Uso:
    from config import CONFIG

    print(CONFIG["stt"]["model"])
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config(path=CONFIG_PATH):
    """Carica config.json e risolve i percorsi relativi alla cartella del progetto."""
    path = Path(path)

    if not path.is_absolute():
        path = BASE_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"File di configurazione non trovato: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    # Controlli essenziali per evitare errori difficili da individuare.
    required_sections = ("stt", "tts", "audio", "paths")
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Sezione mancante in config.json: {section}")

    # Converte i percorsi relativi in percorsi assoluti.
    for section, key in (
        ("tts", "ref_audio"),
        ("paths", "input_dir"),
        ("paths", "reference_audio"),
    ):
        value = config.get(section, {}).get(key)
        if value:
            candidate = Path(value)
            if not candidate.is_absolute():
                config[section][key] = str(BASE_DIR / candidate)

    return config


CONFIG = load_config()
