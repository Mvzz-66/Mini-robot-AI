# main.py
# Punto di ingresso del robot: ascolta una domanda a voce (o da tastiera se
# non c'è il microfono), la passa al "cervello" e fa rispondere il robot.
# Il ciclo continua finché l'utente non dice "esci".

from input.voice import Voice


if __name__ == "__main__":
    voice = Voice()

    while True:
        domanda = voice.voiceRec() #Riconosce la voce
        if not domanda:
            continue
        if "esci" in domanda:
            break
        risposta = voice.risposta(domanda)   # genera la risposta
        voice.speak(risposta)                # la dice ad alta voce
    