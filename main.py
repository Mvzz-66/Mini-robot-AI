# main.py
# Punto di ingresso del robot: ascolta una domanda a voce (o da tastiera se
# non c'è il microfono), la passa al "cervello" e fa rispondere il robot.
# Il ciclo continua finché l'utente non dice "esci".


from input.voice import Voice


if __name__ == "__main__":
    voice = Voice(model="it_IT-serena-high.onnx", pitch=1.5, speed=0.7)

    while True:
        domanda = voice.voiceRec()
        if not domanda:
            continue
        if "esci" in domanda:
            break
        risposta = voice.risposta(domanda)
        voice.speak(risposta)
    