#Brain.py e' il file destinato a contenere la logica del robot,
#  le funzioni di elaborazione del linguaggio naturale e integrazione llm locale con ollama.

import json
import re
from enum import Enum

from ollama import chat  # Importo ollama (si deve scaricare in locale il modello)
from pydantic import BaseModel, Field

from robot.config import CONFIG

AI_CONF = CONFIG["ai"]

MODEL = AI_CONF["model"]  # modello usato per le risposte


# ---------------------------------------------------------------------------
# STATI EMOTIVI (unico punto di verità)
# ---------------------------------------------------------------------------
class BotState(str, Enum):
    IDLE = "idle"
    HAPPY = "happy"          # Felicità
    CURIOUS = "curious"      # Curiosità
    SAD = "sad"              # Tristezza
    SURPRISED = "surprised"  # Sorpresa
    BORED = "bored"          # Noia
    PROUD = "proud"          # Orgoglio
    ANGRY = "angry"          # Rabbia


class EmotionIntensity(str, Enum):
    LOW = "lieve"
    MEDIUM = "media"
    HIGH = "forte"


DEFAULT_STATE = BotState.IDLE
DEFAULT_INTENSITY = EmotionIntensity.LOW
ALLOWED_STATES = {s.value for s in BotState}
ALLOWED_INTENSITIES = {i.value for i in EmotionIntensity}

# PROMPT DI SISTEMA (BMO)
SYSTEM_PROMPT = AI_CONF["system_prompt"]


# SCHEMA JSON PER OLLAMA
class BMOOutputSchema(BaseModel):
    content: str = Field(
        description="La risposta breve, naturale e espressiva di BMO senza emoji."
    )
    state: BotState = Field(
        description="Lo stato emotivo attuale di BMO scelto tra quelli ammessi."
    )
    intensity: EmotionIntensity = Field(
        description="L'intensità dell'emozione provata: lieve, media o forte."
    )


OUTPUT_SCHEMA = BMOOutputSchema.model_json_schema()

FALLBACK_TEXT = "Qualcosa nei miei circuiti ha fatto scintille, puoi ripetere?"

# PULIZIA TESTO
EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"   # emoji e pittogrammi
    "\U00002600-\U000027BF"   # simboli vari e dingbats
    "\U0001F000-\U0001F2FF"   # carte, mahjong, lettere cerchiate
    "\U0000FE0F"              # selettore di variante
    "\U0000200D"              # zero-width joiner
    "]+",
    flags=re.UNICODE,
)


def pulisci(testo):
    testo = EMOJI.sub("", testo)
    testo = testo.replace("*", "")      # toglie anche il grassetto markdown
    return re.sub(r"\s+", " ", testo).strip()


# STATO E CRONOLOGIA
storia = [{"role": "system", "content": SYSTEM_PROMPT}]  # Cronologia della conversazione
stato_corrente = DEFAULT_STATE.value                     # ultimo stato emotivo di BMO


def rispondi_completo(domanda):
    """Invia la domanda al modello e restituisce un dict:
    {"role", "content", "state", "intensity"}. None se la domanda è vuota."""
    global stato_corrente

    if not domanda:
        return None

    # La nota sullo stato precedente va solo nel messaggio inviato al modello,
    # non nella cronologia (così non si accumula a ogni turno).
    nota = f"[Stato emotivo precedente di BMO: {stato_corrente}]"
    messaggi = storia + [{"role": "user", "content": f"{nota}\n{domanda}"}]

    try:
        risposta = chat(
            model=MODEL,
            messages=messaggi,
            format=OUTPUT_SCHEMA,
            think=AI_CONF['think'],
            options={"num_predict": AI_CONF['token'], "temperature": AI_CONF['creativity']},
            keep_alive=AI_CONF['keep_alive'],
        )
        dati = json.loads(risposta.message.content)

        testo = pulisci(dati.get("content", ""))
        if not testo:
            raise ValueError("risposta vuota")

        stato = dati.get("state", DEFAULT_STATE.value)
        if stato not in ALLOWED_STATES:
            stato = DEFAULT_STATE.value

        intensita = dati.get("intensity", DEFAULT_INTENSITY.value)
        if intensita not in ALLOWED_INTENSITIES:
            intensita = DEFAULT_INTENSITY.value

        # Solo se tutto è andato bene si aggiorna la cronologia
        storia.append({"role": "user", "content": domanda})
        storia.append({"role": "assistant", "content": testo})

    except Exception as e:
        print(f"[Fallback BMO]: {e}")
        testo = FALLBACK_TEXT
        stato = DEFAULT_STATE.value
        intensita = DEFAULT_INTENSITY.value

    stato_corrente = stato
    return {
        "role": "assistant",
        "content": testo,
        "state": stato,
        "intensity": intensita,
    }


def rispondi(domanda):
    """Compatibilità col vecchio codice: restituisce solo il testo."""
    risultato = rispondi_completo(domanda)
    return risultato["content"] if risultato else None