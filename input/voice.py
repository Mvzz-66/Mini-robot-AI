# Definisce la classe Voice con le funzioni STT (voiceRec) e TTS (speak).
# voiceRec() riconosce la voce dell'utente; il testo viene passato all'API,
# che genera la risposta, la quale viene letta ad alta voce da speak().

import pyttsx3
import speech_recognition as sr
import robot.brain as brain


class Voice:
    #Constructor
    def __init__(self, language="it-IT"):
        self.language = language #assegno la lingua
        self.recogniser = sr.Recognizer() #Riconoscetore della voce
        self.engine = pyttsx3.init() #generatore della voce

    #Funzione responsabile al riconoscimento vocale
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

        
        except OSError:     #Questa eccezzione é temporanea quando si fixa l'audio si puó tolgiere
            return input("(SOLO CODESPACE)Nessun microfono trovato, scrivi: ")
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

    #Funzione resposabile alla generazione della rispota
    def risposta(self, domanda):
        """Invia la domanda al modello e legge la risposta ad alta voce."""
        risposta = brain.rispondi(domanda)
        if risposta:
            print("BMO:", risposta)
            return risposta
            #self.speak(risposta)