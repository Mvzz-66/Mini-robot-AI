from voice import Voice


if __name__ == "__main__":
    voice = Voice()

while True:
    domanda = voice.voiceRec()
    if not domanda:
        continue
    if "esci" in domanda:
        break
    risposta = chiama_api(domanda)   # la tua funzione verso l'API
    voice.speak(risposta)
    