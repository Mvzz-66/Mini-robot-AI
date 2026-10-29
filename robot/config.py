import json

nome_file = "settings.json"

try:
    with open(nome_file, "r", encoding="utf-8") as file:
        dati = json.load(file)

    progetto = dati["nome_progetto"]
    versione = dati["versione"]
    is_attivo = dati["attivo"]

    lista_utenti = dati["utenti_autorizzati"]

except FileNotFoundError:
    print(f"Errore: Il file '{nome_file}' non è stato trovato.")
except json.JSONDecodeError:
    print("Errore: Il file JSON non è formattato correttamente.")
