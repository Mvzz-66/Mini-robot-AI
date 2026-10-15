from voice import Voice

if __name__ == "__main__":
    voice = Voice()

    try:
        while True:
            text = voice.voiceRec()
            if text is None:
                continue  # riprova se non ha capito

            if "exit" in text or "esci" in text:
                voice.speak("Arrivederci")
                break

            # risposta = chiama_api(text)
            # voice.speak(risposta)
            
    except KeyboardInterrupt:
        print("\nInterrotto")