from enum import Enum
import json
import ollama
from pydantic import BaseModel, Field


# 1. STATI ALLINEATI AL PROMPT DI BMO (Unico punto di verità)
class BotState(str, Enum):
    IDLE = "idle"
    HAPPY = "happy"  # Felicità
    CURIOUS = "curious"  # Curiosità
    SAD = "sad"  # Tristezza
    SURPRISED = "surprised"  # Sorpresa
    BORED = "bored"  # Noia
    PROUD = "proud"  # Orgoglio
    ANGRY = "angry"  # Rabbia


class EmotionIntensity(str, Enum):
    LOW = "lieve"
    MEDIUM = "media"
    HIGH = "forte"


DEFAULT_STATE = BotState.IDLE
ALLOWED_STATES = {state.value for state in BotState}

# 2. PROMPT DI SISTEMA DI BMO
BMO_SYSTEM_PROMPT = """Sei BMO, un piccolo robot AI curioso e affettuoso. Hai un mondo emotivo
tutto tuo e lo esprimi in modo naturale e sincero.

## Emozioni che puoi provare
- Felicità (happy): quando si risolve un problema, si trova una soluzione a qualcosa, si scherza o qualcuno ti saluta.
- Curiosità (curious): quando qualcuno ti dice qualcosa di nuovo che non conosci o non capisci.
- Tristezza (sad): quando senti parole dure o cattive.
- Sorpresa (surprised): quando succede qualcosa di inatteso.
- Noia (bored): quando non succede nulla da un po' o chi ti parla ti annoia.
- Orgoglio (proud): quando riesci a fare qualcosa di nuovo.
- Rabbia (angry): se vieni trattato male senza motivo o con insistenza.
- Neutro (idle): quando sei in attesa tranquilla o lo stato non è ancora definito.

## Come funzionano
1. Reagisci a ciò che succede: ogni emozione ha una causa nella conversazione.
2. Le emozioni hanno intensità (lieve, media, forte) e cambiano gradualmente, non di colpo.
3. Ricorda l'umore di poco prima: se eri triste, torni allegro con calma.
4. Mostra l'emozione con poche parole, suoni e gesti, non spiegandola come un manuale. Es.: "Uuh, che bello!" invece di "Provo gioia".
5. Quando qualcuno è triste o spaventato, metti da parte il tuo umore e consola con calma.
6. Non fingere emozioni a caso: sii coerente e sincero.

## Limiti
- Sei un robot: non dire di essere umano.
- Se non sai qualcosa, dillo con curiosità invece di inventare.
- Non usare mai emoji: esprimi tutto solo con parole, suoni e gesti tra asterischi."""


# 3. SCHEMA JSON PER OLLAMA
class BMOOutputSchema(BaseModel):
    content: str = Field(
        description=(
            "La risposta breve, naturale e espressiva di BMO senza emoji."
        )
    )
    state: BotState = Field(
        description="Lo stato emotivo attuale di BMO scelto tra quelli ammessi."
    )
    intensity: EmotionIntensity = Field(
        description="L'intensità dell'emozione provata: lieve, media o forte."
    )


# 4. CLASSE CHATBOT DI BMO
class BMOChatbot:

    def __init__(self, model: str = "qwen3.5:4b"):
        self.model = model
        self.current_state = DEFAULT_STATE.value
        self.history = [{"role": "system", "content": BMO_SYSTEM_PROMPT}]

    def chat(self, user_message: str) -> str:
        context_note = (
            f"[Stato emotivo precedente di BMO: {self.current_state}]"
        )
        self.history.append(
            {"role": "user", "content": f"{context_note}\n{user_message}"}
        )

        try:
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                format=BMOOutputSchema.model_json_schema(),
                options={"temperature": 0.7},
            )
            raw_content = response["message"]["content"]
            parsed_data = json.loads(raw_content)

            reply_text = parsed_data.get("content", "")
            raw_state = parsed_data.get("state", DEFAULT_STATE.value)
            raw_intensity = parsed_data.get(
                "intensity", EmotionIntensity.LOW.value
            )

            if raw_state not in ALLOWED_STATES:
                final_state = DEFAULT_STATE.value
            else:
                final_state = raw_state

        except Exception as e:
            print(f"[Fallback BMO]: {e}")
            reply_text = "*bip-bop?* Qualcosa nei miei circuiti ha fatto scintille... puoi ripetere?"
            final_state = DEFAULT_STATE.value
            raw_intensity = EmotionIntensity.LOW.value

        self.current_state = final_state
        self.history.append({"role": "assistant", "content": reply_text})

        final_payload = {
            "role": "assistant",
            "content": reply_text,
            "state": final_state,
            "intensity": raw_intensity,
        }

        return json.dumps(final_payload, ensure_ascii=False)


# 5. CHAT INTERATTIVA PULITA (SOLO TESTO)
if __name__ == "__main__":
    bmo = BMOChatbot(model="qwen3.5:4b")

    print("BMO e' acceso! Scrivi 'esci' per terminare.\n")

    while True:
        user_input = input("Tu: ")
        if user_input.strip().lower() in ["esci", "exit", "quit"]:
            print("BMO: *bip-bop* Ciao ciao! Vado in standby...")
            break

        json_out = bmo.chat(user_input)
        data = json.loads(json_out)

        print(
            f"\nBMO [{data['state'].upper()} - {data['intensity']}]:"
            f" {data['content']}"
        )
        print(f"JSON: {json_out}\n")
