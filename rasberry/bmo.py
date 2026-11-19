import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import threading
import queue
import json
import os
import io
import re
import time
from vosk import Model, KaldiRecognizer


# ============================================================
# CONFIGURAZIONE
# ============================================================
SERVER = "http://172.16.13.189:8000/talk"
API_KEY = "fT54Oae50vbaPcXVlKn-kf1lC0dYRoveGoiIw7UlaBw"

NUMERO_MICROFONO = 1      # indice del microfono (sd.query_devices())
SILENZIO_FINE = 1.5       # secondi di pausa che chiudono la domanda
TIMEOUT_ATTESA = 10       # secondi senza parlare dopo "ciao bmo"
MAX_SECONDI_FRASE = 30    # limite di sicurezza del buffer in attesa

ATTIVAZIONE = r"\bciao\s+(bimo|bimbo|vimo|mimo|bmo)\b"
SPEGNIMENTO = r"\bdisattiva(ti)?\s*(ti)?\s*(bimo|bimbo|vimo|mimo|bmo)\b|\bdisattiva\s*tibimo\b"


# ============================================================
# CARTELLE E FILE
# ============================================================
cartella = os.path.dirname(os.path.abspath(__file__))
percorso_modello = os.path.join(cartella, "vosk-model-small-it-0.22")
percorso_file = os.path.join(cartella, "trascrizione.txt")


# ============================================================
# CARICAMENTO MODELLO
# ============================================================
if not os.path.isdir(percorso_modello):
    raise Exception("Modello italiano non trovato!")

print("Caricamento modello...")
model = Model(percorso_modello)


# ============================================================
# VARIABILI
# ============================================================
coda_audio = queue.Queue()     # blocchi audio dal microfono
coda_esiti = queue.Queue()     # risultati del thread di invio

registratore = None
microfono = None
frequenza = None

in_ascolto = False
trascrizione_attiva = False    # True dopo "ciao bmo"
in_risposta = False            # True mentre il server elabora / BMO parla
testo_attesa = ""

audio_frase = bytearray()      # audio dell'ultima frase (prima dell'attivazione)
buffer_comando = bytearray()   # audio registrato dopo l'attivazione
ultimo_parlato = 0.0
t_attivazione = 0.0
parlato = False                # l'utente ha parlato dopo l'attivazione


# ============================================================
# COMUNICAZIONE COL SERVER
# ============================================================
def wav_da_pcm(pcm, sr):
    audio = np.frombuffer(pcm, dtype="int16")
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def invia_e_riproduci(pcm, sr, su_fine):
    """Gira in un thread (la GUI non si blocca).
    Alla fine chiama su_fine((esito, stato_ai))."""

    def lavoro():
        stato_ai = "idle"
        try:
            r = requests.post(
                SERVER,
                headers={"X-API-Key": API_KEY},
                files={"file": ("in.wav", wav_da_pcm(pcm, sr), "audio/wav")},
                timeout=180,
            )

            if r.status_code == 204:
                su_fine(("nessun parlato rilevato", stato_ai))
                return

            r.raise_for_status()

            # per gli sprite: il server potra' mandare lo stato in un header
            stato_ai = r.headers.get("X-AI-State", "idle")

            data, rate = sf.read(io.BytesIO(r.content))
            sd.play(data, rate)
            sd.wait()

            su_fine(("ok", stato_ai))

        except Exception as e:
            su_fine((f"errore: {e}", stato_ai))

    threading.Thread(target=lavoro, daemon=True).start()


def avvia_invio(pcm):
    global in_risposta

    in_risposta = True
    stato.config(text="BMO sta pensando...", fg="orange")
    invia_e_riproduci(pcm, frequenza, coda_esiti.put)


def ripristina(esito, stato_ai):
    """Torna in attesa di 'ciao bmo' dopo la risposta."""
    global in_risposta, trascrizione_attiva, testo_attesa

    in_risposta = False
    trascrizione_attiva = False
    testo_attesa = ""
    buffer_comando.clear()
    audio_frase.clear()

    # scarta l'audio accumulato durante la risposta (eco dell'altoparlante)
    while not coda_audio.empty():
        try:
            coda_audio.get_nowait()
        except queue.Empty:
            break

    try:
        registratore.Reset()
    except Exception:
        pass

    print("Esito:", esito, "| stato AI:", stato_ai)
    # QUI, piu' avanti, cambierai lo sprite in base a stato_ai

    colore = "red" if esito.startswith("errore") else "blue"
    stato.config(text=f"IN ATTESA: DI' CIAO BMO ({esito})", fg=colore)


def chiudi_frase_se_finita():
    """Invia la domanda quando c'e' una pausa dopo che l'utente ha parlato."""
    if not trascrizione_attiva or in_risposta:
        return

    ora = time.time()

    # nessuna domanda dopo l'attivazione: torna in attesa
    if not parlato:
        if ora - t_attivazione > TIMEOUT_ATTESA:
            ripristina("nessuna domanda", "idle")
        return

    if not buffer_comando:
        return

    if ora - ultimo_parlato < SILENZIO_FINE:
        return

    pcm = bytes(buffer_comando)
    buffer_comando.clear()
    avvia_invio(pcm)


# ============================================================
# SALVATAGGIO TESTO
# ============================================================
def salva_testo(testo):
    if testo.strip() == "":
        return

    with open(percorso_file, "a", encoding="utf-8") as file:
        file.write(testo + "\n")

    area_testo.insert("end", testo + "\n")
    area_testo.see("end")


# ============================================================
# RICEZIONE AUDIO
# ============================================================
def ricevi_audio(indata, frames, time_info, status):
    if status:
        print(status)

    coda_audio.put(bytes(indata))


# ============================================================
# AVVIO MICROFONO
# ============================================================
def avvia_ascolto():
    global registratore, microfono, frequenza
    global in_ascolto, trascrizione_attiva

    if in_ascolto:
        return

    try:
        dispositivo = sd.query_devices(NUMERO_MICROFONO)
        frequenza = int(dispositivo["default_samplerate"])

        print("Microfono:", dispositivo["name"])
        print("Frequenza:", frequenza)

        registratore = KaldiRecognizer(model, frequenza)

        microfono = sd.RawInputStream(
            device=NUMERO_MICROFONO,
            samplerate=frequenza,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=ricevi_audio,
        )
        microfono.start()

        in_ascolto = True
        trascrizione_attiva = False

        stato.config(text="IN ATTESA: DI' CIAO BMO", fg="blue")

    except Exception as errore:
        messagebox.showerror("Errore microfono", str(errore))


# ============================================================
# ELABORAZIONE AUDIO
# ============================================================
def elabora_audio():
    global trascrizione_attiva, testo_attesa
    global ultimo_parlato, t_attivazione, parlato

    max_bytes_frase = frequenza * 2 * MAX_SECONDI_FRASE

    while not coda_audio.empty():
        dati = coda_audio.get()

        # mentre BMO elabora/parla, ignora il microfono (evita l'eco)
        if in_risposta:
            continue

        if trascrizione_attiva:
            buffer_comando.extend(dati)
        else:
            audio_frase.extend(dati)
            if len(audio_frase) > max_bytes_frase:
                audio_frase.clear()

        if registratore.AcceptWaveform(dati):
            risultato = json.loads(registratore.Result())
            testo = risultato.get("text", "").lower().strip()

            if not trascrizione_attiva:
                testo_attesa += " " + testo

                corrispondenza = re.search(ATTIVAZIONE, testo_attesa)

                if corrispondenza:
                    trascrizione_attiva = True
                    print("BMO ATTIVATO!")

                    comando = testo_attesa[corrispondenza.end():].strip()
                    testo_attesa = ""

                    if comando:
                        # "ciao bmo, che ore sono" detto tutto di fila:
                        # invio subito l'audio dell'intera frase
                        salva_testo(comando)
                        pcm = bytes(audio_frase)
                        audio_frase.clear()
                        avvia_invio(pcm)
                    else:
                        # solo "ciao bmo": aspetto la domanda
                        buffer_comando.clear()
                        parlato = False
                        t_attivazione = time.time()
                        ultimo_parlato = t_attivazione
                        stato.config(
                            text="BMO ATTIVO - STO ASCOLTANDO",
                            fg="green",
                        )
                else:
                    testo_attesa = testo_attesa[-200:]

                audio_frase.clear()

            else:
                # comando di spegnimento
                if re.search(SPEGNIMENTO, testo):
                    stato.config(text="BMO IN CHIUSURA...", fg="red")
                    print("Comando di spegnimento ricevuto!")
                    finestra.after(100, chiudi)
                    return

                if testo:
                    salva_testo(testo)
                    ultimo_parlato = time.time()
                    parlato = True

        else:
            risultato = json.loads(registratore.PartialResult())
            parziale = risultato.get("partial", "")

            if not trascrizione_attiva:
                stato.config(text="In attesa: " + parziale, fg="blue")
            else:
                if parziale:
                    ultimo_parlato = time.time()
                    parlato = True
                stato.config(text="BMO ATTIVO: " + parziale, fg="green")


# ============================================================
# AGGIORNAMENTO CONTINUO
# ============================================================
def aggiorna():
    if in_ascolto:
        elabora_audio()
        chiudi_frase_se_finita()

    # risultati dal thread di invio (si tocca la GUI solo da qui)
    try:
        esito, stato_ai = coda_esiti.get_nowait()
        ripristina(esito, stato_ai)
    except queue.Empty:
        pass

    finestra.after(100, aggiorna)


# ============================================================
# CHIUSURA PROGRAMMA
# ============================================================
def chiudi():
    global in_ascolto, microfono

    in_ascolto = False

    try:
        if microfono is not None:
            microfono.stop()
            microfono.close()
            microfono = None
    except Exception as errore:
        print("Errore durante la chiusura:", errore)
    finally:
        finestra.destroy()


# ============================================================
# INTERFACCIA GRAFICA
# ============================================================
finestra = tk.Tk()
finestra.title("Mini Robot AI - BMO")
finestra.geometry("750x550")

titolo = tk.Label(finestra, text="MINI ROBOT AI", font=("Arial", 23, "bold"))
titolo.pack(pady=15)

sottotitolo = tk.Label(
    finestra,
    text="Parola d'attivazione offline, risposte dal server",
    font=("Arial", 12),
)
sottotitolo.pack()

stato = tk.Label(
    finestra,
    text="Avvio microfono...",
    font=("Arial", 12, "bold"),
    fg="blue",
)
stato.pack(pady=15)

area_testo = tk.Text(finestra, font=("Arial", 13), wrap="word")
area_testo.pack(padx=20, pady=10, fill="both", expand=True)

# carica le vecchie trascrizioni
if os.path.exists(percorso_file):
    with open(percorso_file, "r", encoding="utf-8") as file:
        area_testo.insert("end", file.read())

finestra.protocol("WM_DELETE_WINDOW", chiudi)

aggiorna()

# avvio automatico del microfono
finestra.after(500, avvia_ascolto)

finestra.mainloop()
