# Definisce la classe Voice con le funzioni STT (voiceRec) e TTS (speak).
# voiceRec() riconosce la voce dell'utente; il testo viene passato all'API,
# che genera la risposta, la quale viene letta ad alta voce da speak().

import os
import platform
import subprocess
import sys
import tempfile
import wave

import speech_recognition as sr
import robot.brain as brain


def higher_pitch(src, dst, factor=1.25):
    """Alza tono e velocità cambiando il sample rate del wav."""
    with wave.open(src, "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())
    with wave.open(dst, "wb") as o:
        o.setnchannels(params.nchannels)
        o.setsampwidth(params.sampwidth)
        o.setframerate(int(params.framerate * factor))
        o.writeframes(frames)


class Voice:
    # Constructor
    def __init__(self, language="it-IT", model="it_IT-serena-high.onnx", pitch=1.0, speed=1.0): #valori predefiniti
        self.language = language
        self.recogniser = sr.Recognizer()
        self.model = model   # modello Piper da usare
        self.pitch = pitch   # 1.0 = tono normale, più alto = più acuto
        self.speed = speed   # 1.0 = velocità normale, sotto 1 = più lento

    # Funzione responsabile al riconoscimento vocale
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

        except OSError:
            return input("(SOLO CODESPACE)Nessun microfono trovato, scrivi: ")
        except sr.WaitTimeoutError:
            print("Nessun suono rilevato")
        except sr.UnknownValueError:
            print("Non ho capito l'audio")
        except sr.RequestError as e:
            print(f"Errore richiesta al servizio: {e}")
        return None

    def speak(self, text):
        """Legge ad alta voce il testo con Piper (offline)."""
        if not text:
            return
        tmp = tempfile.gettempdir()
        wav = os.path.join(tmp, "bmo_tts.wav")
        wav_bmo = os.path.join(tmp, "bmo_tts_pitch.wav")

        # Alzare il tono con il sample rate accelera anche la voce:
        # lo compensiamo rallentando la generazione di Piper.
        length_scale = self.pitch / self.speed

        # 1. genera il file audio con Piper
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", self.model,
             "--length-scale", str(length_scale), "-f", wav],
            input=text.encode("utf-8"),
            check=True,
        )

        # 2. alza il tono solo se serve
        if self.pitch != 1.0:
            higher_pitch(wav, wav_bmo, self.pitch)
        else:
            wav_bmo = wav

        # 3. riproduce il file
        if platform.system() == "Windows":
            import winsound
            winsound.PlaySound(wav_bmo, winsound.SND_FILENAME)
        else:
            subprocess.run(["aplay", "-q", wav_bmo], check=True)

    # Funzione responsabile alla generazione della risposta
    def risposta(self, domanda):
        """Invia la domanda al modello e restituisce la risposta."""
        risposta = brain.rispondi(domanda)
        if risposta:
            print("BMO:", risposta)
            return risposta
