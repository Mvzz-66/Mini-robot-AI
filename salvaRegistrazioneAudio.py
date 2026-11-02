import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import queue
import json
import os
import re

from vosk import Model, KaldiRecognizer


# CARTELLE E FILE
cartella = os.path.dirname(os.path.abspath(__file__))

percorso_modello = os.path.join(
    cartella,
    "vosk-model-small-it-0.22"
)

percorso_file = os.path.join(
    cartella,
    "trascrizione.txt"
)


# CARICAMENTO MODELLO
if not os.path.isdir(percorso_modello):
    raise Exception("Modello italiano non trovato!")

print("Caricamento modello...")
model = Model(percorso_modello)


# VARIABILI
coda_audio = queue.Queue()

registratore = None
microfono = None
frequenza = None

in_ascolto = False
trascrizione_attiva = False
testo_attesa = ""


# SALVATAGGIO TESTO
def salva_testo(testo):

    if testo.strip() == "":
        return

    with open(percorso_file, "a", encoding="utf-8") as file:
        file.write(testo + "\n")

    area_testo.insert("end", testo + "\n")
    area_testo.see("end")


# RICEZIONE AUDIO
def ricevi_audio(indata, frames, time, status):

    if status:
        print(status)

    coda_audio.put(bytes(indata))


# AVVIO MICROFONO
def avvia_ascolto():

    global registratore
    global microfono
    global frequenza
    global in_ascolto
    global trascrizione_attiva

    if in_ascolto:
        return

    try:

        # Seleziona il microfono
        numero_microfono = 1

        dispositivo = sd.query_devices(numero_microfono)

        frequenza = int(dispositivo["default_samplerate"])

        print("Microfono:", dispositivo["name"])
        print("Frequenza:", frequenza)

        # Crea il riconoscitore
        registratore = KaldiRecognizer(
            model,
            frequenza
        )

        # Apre il microfono
        microfono = sd.RawInputStream(
            device=numero_microfono,
            samplerate=frequenza,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=ricevi_audio
        )

        microfono.start()

        in_ascolto = True
        trascrizione_attiva = False

        stato.config(
            text="IN ATTESA: DI' CIAO BMO",
            fg="blue"
        )

    except Exception as errore:

        messagebox.showerror(
            "Errore microfono",
            str(errore)
        )


# ELABORAZIONE AUDIO
def elabora_audio():

    global trascrizione_attiva
    global testo_attesa

    while not coda_audio.empty():

        dati = coda_audio.get()

        if registratore.AcceptWaveform(dati):

            risultato = json.loads(registratore.Result())

            testo = risultato.get("text", "").lower().strip()

            if not trascrizione_attiva:

                testo_attesa += " " + testo

                # Cerca la parola di attivazione
                corrispondenza = re.search(
                    r"\bciao\s+(bimo|bimbo|vimo|mimo)\b",
                    testo_attesa
                )

                if corrispondenza:

                    trascrizione_attiva = True

                    stato.config(
                        text="BMO ATTIVO - STO ASCOLTANDO",
                        fg="green"
                    )

                    print("BMO ATTIVATO!")

                    # Recupera le parole dopo CIAO BMO
                    comando = testo_attesa[corrispondenza.end():].strip()

                    salva_testo(comando)

                    testo_attesa = ""

                else:

                    # Evita che il testo in attesa cresca all'infinito
                    testo_attesa = testo_attesa[-200:]

            else:

                # CONTROLLO COMANDO DI SPEGNIMENTO
                if re.search(r"\bdisattivati\s+bimbo\b", testo):

                    stato.config(
                        text="BMO IN CHIUSURA...",
                        fg="red"
                    )

                    print("Comando di spegnimento ricevuto!")

                    finestra.after(100, chiudi)

                    return

                # TRASCRIZIONE NORMALE
                salva_testo(testo)

        else:

            risultato = json.loads(registratore.PartialResult())

            parziale = risultato.get("partial", "")

            if not trascrizione_attiva:

                stato.config(
                    text="In attesa: " + parziale,
                    fg="blue"
                )

            else:

                stato.config(
                    text="BMO ATTIVO: " + parziale,
                    fg="green"
                )


# FERMA MICROFONO
def ferma_ascolto():

    global in_ascolto
    global microfono
    global trascrizione_attiva

    if not in_ascolto:
        return

    in_ascolto = False

    microfono.stop()
    microfono.close()
    microfono = None

    # Elabora l'audio rimasto nella coda
    elabora_audio()

    # Recupera l'ultima frase
    if trascrizione_attiva:

        risultato = json.loads(
            registratore.FinalResult()
        )

        testo = risultato.get("text", "")

        salva_testo(testo)

    trascrizione_attiva = False

    stato.config(
        text="MICROFONO SPENTO",
        fg="red"
    )

    pulsante_start.config(state="normal")
    pulsante_stop.config(state="disabled")


# AGGIORNAMENTO CONTINUO
def aggiorna():

    if in_ascolto:
        elabora_audio()

    finestra.after(100, aggiorna)


# CHIUSURA PROGRAMMA
def chiudi():

    global in_ascolto
    global microfono

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


# INTERFACCIA GRAFICA
finestra = tk.Tk()

finestra.title("Mini Robot AI - Riconoscimento vocale")
finestra.geometry("750x550")

titolo = tk.Label(
    finestra,
    text="MINI ROBOT AI",
    font=("Arial", 23, "bold")
)
titolo.pack(pady=15)

sottotitolo = tk.Label(
    finestra,
    text="Riconoscimento vocale offline",
    font=("Arial", 12)
)
sottotitolo.pack()

stato = tk.Label(
    finestra,
    text="Avvio microfono...",
    font=("Arial", 12, "bold"),
    fg="blue"
)
stato.pack(pady=15)

# AREA DI TESTO
area_testo = tk.Text(
    finestra,
    font=("Arial", 13),
    wrap="word"
)

area_testo.pack(
    padx=20,
    pady=10,
    fill="both",
    expand=True
)

# CARICA LE VECCHIE TRASCRIZIONI
if os.path.exists(percorso_file):

    with open(percorso_file, "r", encoding="utf-8") as file:
        area_testo.insert("end", file.read())

# CHIUSURA PROGRAMMA
finestra.protocol("WM_DELETE_WINDOW", chiudi)

aggiorna()

# AVVIO AUTOMATICO DEL MICROFONO
finestra.after(500, avvia_ascolto)

finestra.mainloop()