#Questo file definisce la classe della voce, definisce le funzioni di e STT e TTS.
#Funzione voiceRec() riconosce la voice dell'utente, poi il risultato viene passato all'API che poi va a
#generare la risposta che a sua volta viene passata alla funzione Speak() che ripodurrera la risposta dell'API.

import speech_recognition as sr
import pyttsx3


class Voice:
    def __init__(self, language="it-IT"):
        self.language = language
        self.recogniser = sr.Recognizer()
        self.engine = pyttsx3.init()

    def voiceRec(self):
        """Ascolta il microfono, rileva la voce e restituisce il testo in minuscolo."""
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
        self.engine.say(text)
        self.engine.runAndWait()
        


    #Funzione per il riconoscimento della voce
    #def voiceRec():
