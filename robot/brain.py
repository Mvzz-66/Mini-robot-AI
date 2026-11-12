#Brain.py e' il file destinato a contenere la logica del robot,
#  le funzioni di elaborazione del linguaggio naturale e integrazione llm locale con ollama.

from ollama import chat #Impoto ollama (si deve scaricare in locale il modello)
from robot.config import CONFIG
import re

AI_CONF= CONFIG["ai"]

MODEL = AI_CONF["model"]  # modello usato per le risposte 
SYSTEM_PROMPT = AI_CONF["system_prompt"]

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

storia = [{"role": "system", "content": SYSTEM_PROMPT}] #Cronologia della conversazione


def pulisci(testo):
    testo = EMOJI.sub("", testo)
    testo = testo.replace("*", "")      # toglie anche il grassetto markdown
    return re.sub(r"\s+", " ", testo).strip()


def rispondi(domanda):
    """Invia la domanda al modello LLM e restituisce la risposta come testo."""
    if not domanda:
        return None

    storia.append({"role": "user", "content": domanda})     #Si aggiunge allo storico la domanda dell'utente
    risposta = chat(model=MODEL, messages=storia, think=False,
                  options={"num_predict": 80}, keep_alive="30m")
    testo = pulisci(risposta.message.content)
    storia.append({"role": "assistant", "content": testo})  #Si aggiunge la domanda allo storico
    return testo