from input.voice import Voice
from robot import brain

voice = Voice()

while True:
    audio = voice.record_array(seconds=5)
    domanda = voice.voiceRec(audio)
    print("Tu:", domanda)

    if not domanda:
        continue
    if "esci" in domanda.lower():
        break

    risposta = brain.rispondi(domanda)
    print("BMO:", risposta)
    voice.speak(risposta)