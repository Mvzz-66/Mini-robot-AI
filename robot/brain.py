#Brain.py e' il file destinato a contenere la logica del robot,
#  le funzioni di elaborazione del linguaggio naturale e integrazione llm locale con ollama.

from ollama import chat #Impoto ollama (si deve scaricare in locale il modello)

MODEL = "llama3.2"  # modello usato per le risposte (scaricalo con: ollama pull llama3.2)

SYSTEM_PROMPT = (
    "Sei un piccolo robot chiamato BMO, creato per aiutare gli utenti "
    "a risolvere problemi e fornire informazioni. Rispondi sempre in italiano, "
    "in modo breve e chiaro."
)

storia = [{"role": "system", "content": SYSTEM_PROMPT}] #Cronologia della conversazione


def rispondi(domanda):
    """Invia la domanda al modello LLM e restituisce la risposta come testo."""
    if not domanda:
        return None

    storia.append({"role": "user", "content": domanda})     #Si aggiunge allo storico la domanda dell'utente
    risposta = chat(model=MODEL, messages=storia)           #Genera la risposta
    testo = risposta.message.content
    storia.append({"role": "assistant", "content": testo})  #Si aggiunge la domanda allo storico
    return testo