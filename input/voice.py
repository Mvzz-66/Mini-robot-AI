# Definisce la classe Voice con le funzioni STT (voiceRec) e TTS (speak).
# voiceRec() riconosce la voce dell'utente; il testo viene passato all'API,
# che genera la risposta, la quale viene letta ad alta voce da speak().

import pyttsx3
import speech_recognition as sr
import robot.barin as brain


class Voice:
    def __init__(self, language="it-IT"):
        self.language = language
        self.recogniser = sr.Recognizer()
        self.engine = pyttsx3.init()

    def voiceRec(self):
        """Ascolta il microfono e restituisce il testo in minuscolo (o None)."""
        try:
            with sr.Microphone() as source:
                print("Ascolto...")
                self.recogniser.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recogniser.listen(source, timeout=5, phrase_time_limit=15)

            text = self.recogniser.recognize_google(audio, language=self.language).lower()
            print("Hai detto:", text)
            return text

        except sr.WaitTimeoutError:
            print("Nessun suono rilevato")
        except sr.UnknownValueError:
            print("Non ho capito l'audio")
        except sr.RequestError as e:
            print(f"Errore richiesta al servizio: {e}")
        return None

    def speak(self, text):
        """Legge ad alta voce il testo."""
        if not text:
            return
        self.engine.say(text)
        self.engine.runAndWait()

    def risposta(self, domanda):
        """Invia la domanda al modello e legge la risposta ad alta voce."""
        risposta = brain.rispondi(domanda)
        if risposta:
            print("BMO:", risposta)
            self.speak(risposta)