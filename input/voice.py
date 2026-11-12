# Definisce la classe Voice con le funzioni STT (voiceRec) e TTS (speak).
# voiceRec() trascrive l'audio con faster-whisper; speak() legge il testo
# ad alta voce con Piper (offline).

import os
import platform
import subprocess
import sys
import tempfile
import wave

import sounddevice as sd
import soundfile as sf

from faster_whisper import WhisperModel

from robot.config import CONFIG


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

    def __init__(self):
        # Configurazione STT
        stt = CONFIG["stt"]
        self.whisper_model = WhisperModel(
            stt["model"],
            device=stt["device"],
            compute_type=stt["compute_type"],
        )
        self.beam_size = stt["beam_size"]
        self.language = stt.get("language")

        # Configurazione TTS (Piper)
        tts = CONFIG["tts"]
        self.piper_model = tts["piper_model"]
        self.pitch = tts.get("pitch", 1.5)   # 1.0 = normale, più alto = più acuto
        self.speed = tts.get("speed", 0.7)   # 1.0 = normale, sotto 1 = più lento

    # -------------------------
    # SPEECH TO TEXT
    # -------------------------

    def record_array(self, seconds=5, samplerate=16000):
        """Registra dal microfono e restituisce un array 1D float32."""
        print("Parla...")
        audio = sd.rec(int(seconds * samplerate), samplerate=samplerate,
                       channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()

    def voiceRec(self, audio):
        """Trascrive un array numpy (o un file audio) in testo."""
        segments, info = self.whisper_model.transcribe(
            audio,
            beam_size=self.beam_size,
            language=self.language,
        )
        text = " ".join(segment.text for segment in segments)
        print(
            f"Detected language: {info.language} "
            f"(probability: {info.language_probability:.2f})"
        )
        return text.strip()

    # -------------------------
    # TEXT TO SPEECH
    # -------------------------

    def speak(self, text):
        """Legge ad alta voce il testo con Piper (offline)."""
        if not text:
            return None

        wav = os.path.join(tempfile.gettempdir(), "bmo_tts.wav")

        # Alzare il tono con il sample rate accelera anche la voce:
        # lo compensiamo rallentando la generazione di Piper.
        length_scale = self.pitch / self.speed

        # 1. genera il file audio con Piper
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", self.piper_model,
             "--length-scale", str(length_scale), "-f", wav],
            input=text.encode("utf-8"),
            check=True,
        )

        # 2. legge il wav
        audio, sr = sf.read(wav, dtype="float32")

        # 3. riproduce (volume + tono), con fallback di sistema
        if CONFIG["audio"]["playback"]:
            try:
                audio_out = audio * CONFIG["audio"]["volume"]
                sd.play(audio_out, int(sr * self.pitch))  # sample rate più alto = tono più acuto
                sd.wait()
            except Exception as e:
                print(f"sounddevice non disponibile ({e}), uso il player di sistema")
                self._play_system(wav)

        return audio

    def synthesize(self, text):
        """Genera il parlato con Piper e restituisce il percorso di un wav
        (tono già alzato). Il chiamante deve cancellare il file."""
        if not text:
            return None

        fd, raw = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        fd, out = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        try:
            length_scale = self.pitch / self.speed

            # 1. genera il wav con Piper
            subprocess.run(
                [sys.executable, "-m", "piper", "-m", self.piper_model,
                 "--length-scale", str(length_scale), "-f", raw],
                input=text.encode("utf-8"),
                check=True,
            )

            # 2. alza il tono (stessa logica di speak, ma su file)
            if self.pitch != 1.0:
                higher_pitch(raw, out, self.pitch)
            else:
                os.replace(raw, out)
        except Exception:
            if os.path.exists(out):
                os.remove(out)
            raise
        finally:
            if os.path.exists(raw):
                os.remove(raw)

        return out

    def _play_system(self, wav):
        """Fallback: riproduce il wav con winsound (Windows) o aplay (Linux)."""
        wav_bmo = wav
        if self.pitch != 1.0:
            wav_bmo = os.path.join(tempfile.gettempdir(), "bmo_tts_pitch.wav")
            higher_pitch(wav, wav_bmo, self.pitch)

        if platform.system() == "Windows":
            import winsound
            winsound.PlaySound(wav_bmo, winsound.SND_FILENAME)
        else:
            subprocess.run(["aplay", "-q", wav_bmo], check=True)