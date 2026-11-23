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
from PIL import Image, ImageTk   # pip install pillow


# ============================================================
# CONFIGURAZIONE
# ============================================================
SERVER = "http://172.16.13.189:8000/talk"


API_KEY = os.environ.get("BMO_API_KEY", "fT54Oae50vbaPcXVlKn-kf1lC0dYRoveGoiIw7UlaBw")

NUMERO_MICROFONO = 1      # indice del microfono (sd.query_devices())
SILENZIO_FINE = 1.5       # secondi di pausa che chiudono la domanda
MAX_SECONDI_FRASE = 30    # limite di sicurezza del buffer in attesa

# ------------------------------------------------------------
# VOLTO
# ------------------------------------------------------------
COLORE_SFONDO_VOLTO = "#C0F9DE"
SCHERMO_INTERO = True     # F11 = schermo intero on/off, Esc = esci dallo schermo intero
SALVA_TRASCRIZIONE = True # continua a scrivere trascrizione.txt (senza mostrarla)

SECONDI_EMOZIONE = 6      # quanto resta l'emozione DOPO che BMO ha finito di parlare
SECONDI_PER_NOIA = 120    # attivo da tanto senza che nessuno parli -> noia
VELOCITA_BOCCA = 4        # cambi di sprite al secondo mentre parla
SOGLIA_BATTERIA = 15      # % sotto cui BMO mostra la faccia "batteria in scarica"

SPRITE_IDLE = "Rosto-01.png"                        # idle / sta pensando
SPRITE_PARLATO = ("Rosto-01.png", "Rosto-02.png")   # mentre parla si alternano
SPRITE_SPENTO = "Rosto-29.png"                      # in attesa di "ciao bmo" / disattivato

# Emozione -> (sprite grado BASSO, sprite grado ALTO), come nel PDF BMO_video
EMOZIONI = {
    "neutro":     ("Rosto-01.png", "Rosto-01.png"),
    "orgoglioso": ("Rosto-04.png", "Rosto-04.png"),  # orgoglio / felice (happy, proud)
    "curioso":    ("Rosto-13.png", "Rosto-13.png"),  # occhi grandi (il PDF non ha uno sprite apposta)
    "sorpreso":   ("Rosto-05.png", "Rosto-13.png"),  # basso: complimento carino, alto: stupore
    "triste":     ("Rosto-03.png", "Rosto-06.png"),
    "arrabbiato": ("Rosto-10.png", "Rosto-07.png"),
    "annoiato":   ("Rosto-08.png", "Rosto-08.png"),  # la persona lo annoia
    "noia":       ("Rosto-16.png", "Rosto-16.png"),  # attivo da tanto / ignorato
    "batteria":   ("Rosto-15.png", "Rosto-15.png"),  # batteria in scarica
    "errore":     ("Rosto-25.png", "Rosto-25.png"),
    "spento":     ("Rosto-29.png", "Rosto-29.png"),
}

# Sinonimi (italiano / inglese) che il server puo' mandare in X-AI-State
SINONIMI = {
    "idle": "neutro", "neutral": "neutro", "calm": "neutro", "calmo": "neutro",
    "felice": "orgoglioso", "happy": "orgoglioso", "contento": "orgoglioso",
    "orgoglio": "orgoglioso", "proud": "orgoglioso", "joy": "orgoglioso",
    "curious": "curioso", "curiosita": "curioso", "curiosità": "curioso",
    "soddisfatto": "orgoglioso",
    "surprised": "sorpreso", "surprise": "sorpreso", "stupito": "sorpreso",
    "imbarazzato": "sorpreso", "shy": "sorpreso", "complimento": "sorpreso",
    "sad": "triste", "dispiaciuto": "triste",
    "angry": "arrabbiato", "anger": "arrabbiato", "rabbia": "arrabbiato",
    "irritato": "arrabbiato",
    "bored": "annoiato", "annoyed": "annoiato", "seccato": "annoiato",
    "noia": "noia", "lonely": "noia", "ignorato": "noia", "ignored": "noia",
    "battery": "batteria", "low_battery": "batteria", "batteria_scarica": "batteria",
    "error": "errore", "sleep": "spento",
}

# Gradi a parole -> valore 0..1 (da 0.5 in su si usa lo sprite "alto")
GRADI_PAROLE = {
    "lieve": 0.1, "basso": 0.1, "bassa": 0.1, "leggero": 0.1, "poco": 0.1, "low": 0.1, "mild": 0.1,
    "medio": 0.4, "media": 0.4, "medium": 0.4, "mid": 0.4,
    "alto": 0.95, "alta": 0.95, "forte": 0.95, "molto": 0.95, "high": 0.95, "strong": 0.95,
}

ATTIVAZIONE = r"\b(ciao|cio|ciò|)\s+(bimo|bimbo|vimo|mimo|bmo|primo)\b"
SPEGNIMENTO = r"\b(?:disattiva(?:ti)?|spegni|spegni(?:ti)?)\s+(?:il\s+)?(?:bimo|bimbo|vimo|mimo|bmo|primo)\b"


# ============================================================
# CARTELLE E FILE
# ============================================================
cartella = os.path.dirname(os.path.abspath(__file__))
percorso_modello = os.path.join(cartella, "vosk-model-small-it-0.22")
percorso_file = os.path.join(cartella, "trascrizione.txt")
cartella_volti = os.path.join(cartella, "volti")


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
coda_volto = queue.Queue()     # "BMO inizia a parlare" dal thread di invio

sprite = {}                    # nome file -> immagine pronta per Tk (alla misura attuale)
originali = {}                 # nome file -> immagine PIL originale
dimensione_sprite = None       # (larghezza, altezza) attuale degli sprite
id_ridimensiona = None         # timer anti-rimbalzo del ridimensionamento
sprite_mostrato = None         # sprite attualmente sul volto
in_parlato = False             # True mentre l'audio della risposta e' in riproduzione
volto_temp = None              # sprite dell'emozione mostrata dopo il parlato
volto_fino_a = 0.0             # fino a quando resta l'emozione
ultima_attivita = time.time()  # ultima interazione (per la noia)
batteria_bassa = False
ultimo_controllo_batteria = 0.0

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
parlato = False                # l'utente ha parlato dopo l'attivazione


# ============================================================
# VOLTO: STATO AI -> EMOZIONE + GRADO -> SPRITE
# ============================================================
def normalizza_emozione(nome):
    nome = str(nome or "").strip().lower()
    nome = SINONIMI.get(nome, nome)
    return nome if nome in EMOZIONI else "neutro"


def normalizza_grado(valore):
    """Trasforma il grado in un numero 0..1 (None se non indicato).
    Accetta: frazione (0.8), intero 1..5 (4), oppure parole (basso/medio/alto)."""
    if valore is None or valore == "":
        return None

    decimale = isinstance(valore, float)   # 0.8 / 1.0 = frazione, 1 / 4 = scala 1..5

    if isinstance(valore, str):
        v = valore.strip().lower()
        if v in GRADI_PAROLE:
            return GRADI_PAROLE[v]
        decimale = "." in v
        try:
            valore = float(v)
        except ValueError:
            return None

    try:
        x = float(valore)
    except (TypeError, ValueError):
        return None

    if not decimale and x >= 1:            # numero intero: scala 1..5
        x = (min(x, 5) - 1) / 4
    return max(0.0, min(1.0, x))


def interpreta_stato(valore):
    """Legge X-AI-State e restituisce (emozione, grado 0..1 o None).
    Formati accettati:
        "triste"          "triste:alto"        "triste:0.8"
        "sad,4"           "angry high"
        {"emotion": "sad", "intensity": 0.8}   (JSON)
    """
    if not valore:
        return "neutro", None

    testo = valore.strip()

    try:
        obj = json.loads(testo)
        if isinstance(obj, dict):
            emo = obj.get("emotion") or obj.get("emozione") or obj.get("state") or obj.get("stato")
            grado = obj.get("intensity", obj.get("intensita", obj.get("grado")))
            return normalizza_emozione(emo), normalizza_grado(grado)
    except ValueError:
        pass

    minuscolo = testo.lower()
    parole = [p for p in re.split(r"[:,;|\s_=/-]+", minuscolo) if p]

    # emozione: prima parola riconosciuta, altrimenti la cerco dentro al testo
    # (cosi' "sadness", "triste_alto", "emotion=sad" funzionano lo stesso)
    emozione = None
    for p in parole:
        candidata = SINONIMI.get(p, p)
        if candidata in EMOZIONI:
            emozione = candidata
            break
    if emozione is None:
        chiavi = sorted(list(SINONIMI) + list(EMOZIONI), key=len, reverse=True)
        for chiave in chiavi:
            if chiave in minuscolo:
                emozione = normalizza_emozione(chiave)
                break
    if emozione is None:
        emozione = "neutro"

    # grado: prima parola che sia un grado valido (alto, basso, 0.8, 4...)
    grado = None
    for p in parole:
        g = normalizza_grado(p)
        if g is not None:
            grado = g
            break

    return emozione, grado


def scegli_sprite(emozione, grado):
    """Emozione + grado -> nome del file dello sprite (basso < 0.5 <= alto)."""
    basso, alto = EMOZIONI[emozione]
    if grado is not None and grado >= 0.5:
        return alto
    return basso


def carica_sprite():
    """Carica e ridimensiona una sola volta tutti gli sprite usati."""
    nomi = {SPRITE_IDLE, SPRITE_SPENTO, *SPRITE_PARLATO}
    nomi.update(n for coppia in EMOZIONI.values() for n in coppia)

    for nome in nomi:
        percorso = os.path.join(cartella_volti, nome)
        if not os.path.exists(percorso):
            print("Sprite mancante:", percorso)
            continue

        originali[nome] = Image.open(percorso).convert("RGBA")


def ridimensiona_sprite(larghezza, altezza):
    """Adatta tutti gli sprite alla finestra (mantiene il 16:9)."""
    global dimensione_sprite, sprite_mostrato

    if not originali or larghezza < 50 or altezza < 50:
        return

    w0, h0 = next(iter(originali.values())).size
    scala = min(larghezza / w0, altezza / h0)
    nuova = (int(w0 * scala), int(h0 * scala))

    if nuova == dimensione_sprite:
        return

    dimensione_sprite = nuova
    for nome, img in originali.items():
        sprite[nome] = ImageTk.PhotoImage(img.resize(nuova, Image.LANCZOS))

    corrente = sprite_mostrato
    sprite_mostrato = None          # forza il ridisegno con la nuova misura
    if corrente:
        imposta_sprite(corrente)


def finestra_ridimensionata(evento):
    """Ridimensiona gli sprite poco dopo che la finestra ha smesso di cambiare."""
    global id_ridimensiona

    if evento.widget is not finestra:
        return

    if id_ridimensiona is not None:
        finestra.after_cancel(id_ridimensiona)

    id_ridimensiona = finestra.after(
        150,
        lambda: ridimensiona_sprite(finestra.winfo_width(), finestra.winfo_height()),
    )


def schermo_intero(attivo):
    finestra.attributes("-fullscreen", attivo)


def attiva_disattiva_debug():
    """Tasto D: mostra/nasconde la riga di stato in basso."""
    if stato.winfo_ismapped():
        stato.place_forget()
    else:
        stato.place(relx=0.5, rely=0.99, anchor="s")


def imposta_sprite(nome):
    """Cambia l'immagine solo se e' diversa da quella gia' mostrata."""
    global sprite_mostrato

    if nome == sprite_mostrato:
        return

    immagine = sprite.get(nome) or sprite.get(SPRITE_IDLE)
    if immagine is None:
        return

    sprite_mostrato = nome
    volto.config(image=immagine)
    volto.image = immagine         # evita che Tk lo butti via


def emozione_dopo_parlato(valore):
    """Dopo il parlato BMO passa all'emozione indicata dal server."""
    global volto_temp, volto_fino_a

    emozione, grado = interpreta_stato(valore)
    nome = scegli_sprite(emozione, grado)
    print(f"Emozione finale: {emozione} (grado {grado}) -> {nome}")

    if emozione == "neutro":
        volto_temp = None
    else:
        volto_temp = nome
        volto_fino_a = time.time() + SECONDI_EMOZIONE


def batteria_scarica():
    """True se la batteria e' sotto soglia e non e' in carica.
    Serve psutil (pip install psutil); se non c'e' o non c'e' batteria -> False."""
    try:
        import psutil
        b = psutil.sensors_battery()
        return b is not None and not b.power_plugged and b.percent <= SOGLIA_BATTERIA
    except Exception:
        return False


def aggiorna_volto():
    """Decide ogni 100 ms quale sprite mostrare, in base allo stato di BMO."""
    global batteria_bassa, ultimo_controllo_batteria

    ora = time.time()

    if ora - ultimo_controllo_batteria > 30:
        ultimo_controllo_batteria = ora
        batteria_bassa = batteria_scarica()

    if in_risposta:
        if in_parlato:
            # mentre parla: si alternano idle e bocca aperta
            nome = SPRITE_PARLATO[int(ora * VELOCITA_BOCCA) % 2]
        else:
            nome = SPRITE_IDLE                       # sta pensando
    elif volto_temp and ora < volto_fino_a:
        nome = volto_temp                            # emozione dopo il parlato
    elif not trascrizione_attiva:
        nome = SPRITE_SPENTO                         # aspetta "ciao bmo"
    elif batteria_bassa:
        nome = EMOZIONI["batteria"][0]
    elif ora - max(ultimo_parlato, ultima_attivita) > SECONDI_PER_NOIA:
        nome = EMOZIONI["noia"][0]                   # nessuno gli parla da tanto
    else:
        nome = SPRITE_IDLE

    imposta_sprite(nome)


# ============================================================
# COMUNICAZIONE COL SERVER
# ============================================================
def leggi_stato_da_header(headers):
    """Cerca nella risposta del server stato e intensita' (brain.py: state + intensity),
    qualunque nome abbia l'header (X-AI-State, X-State, X-Emotion, X-AI-Intensity...).
    Restituisce una stringa tipo "sad:forte", oppure None se non c'e' niente."""
    stato = intensita = None

    for nome, valore in headers.items():
        n = nome.lower()
        if "intens" in n or "grado" in n:
            intensita = valore
        elif any(k in n for k in ("state", "stato", "emotion", "emozione")):
            stato = valore

    if stato is None:
        return None
    return f"{stato}:{intensita}" if intensita else stato


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

            # il server manda emozione e grado nell'header X-AI-State
            print("Header ricevuti dal server:", dict(r.headers))
            stato_ai = leggi_stato_da_header(r.headers)
            if stato_ai is None:
                print("ATTENZIONE: il server non ha mandato nessun header di stato/emozione "
                      "(il volto resta idle). Va aggiunto nella risposta di /talk.")
                stato_ai = "idle"

            data, rate = sf.read(io.BytesIO(r.content))

            # da qui la bocca si anima; l'emozione arriva a fine audio
            coda_volto.put("inizio_parlato")
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
    """Resta attivo finché non viene richiesto di essere disattivato."""
    global in_risposta, trascrizione_attiva, testo_attesa, parlato
    global in_parlato, volto_temp, ultima_attivita

    in_risposta = False
    in_parlato = False
    trascrizione_attiva = True  # BMO resta attivo dopo ogni risposta
    ultima_attivita = time.time()
    parlato = False
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

    # finito di parlare: il volto passa all'emozione (es. triste) e ci resta un po'
    if esito.startswith("errore"):
        emozione_dopo_parlato("errore")
    elif esito == "ok":
        emozione_dopo_parlato(stato_ai)
    else:
        volto_temp = None

    colore = "red" if esito.startswith("errore") else "green"
    stato.config(
        text=f"BMO ATTIVO - IN ASCOLTO ({esito}) | stato dal server: {stato_ai!r}",
        fg=colore,
    )


def chiudi_frase_se_finita():
    """Invia la domanda quando c'e' una pausa dopo che l'utente ha parlato."""
    global parlato

    if not trascrizione_attiva or in_risposta:
        return

    ora = time.time()

    # nessuna domanda dopo l'attivazione: torna in attesa
    if not parlato:
        return

    if not buffer_comando:
        return

    if ora - ultimo_parlato < SILENZIO_FINE:
        return

    pcm = bytes(buffer_comando)
    buffer_comando.clear()
    parlato = False  # attende una nuova frase dopo questa domanda
    avvia_invio(pcm)


# ============================================================
# SALVATAGGIO TESTO
# ============================================================
def salva_testo(testo):
    if testo.strip() == "":
        return

    if SALVA_TRASCRIZIONE:
        with open(percorso_file, "a", encoding="utf-8") as file:
            file.write(testo + "\n")


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
    global ultimo_parlato, parlato, volto_temp, ultima_attivita

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
                    ultima_attivita = time.time()
                    volto_temp = None
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
                        ultimo_parlato = time.time()
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
                    trascrizione_attiva = False
                    parlato = False
                    stato.config(text="BMO DISATTIVATO - DI' CIAO BMO PER RIATTIVARLO", fg="red")
                    print("BMO DISATTIVATO!")
                    volto_temp = None
                    testo_attesa = ""
                    audio_frase.clear()
                    buffer_comando.clear()
                    try:
                        registratore.Reset()
                    except Exception:
                        pass
                    continue

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
    global in_parlato

    if in_ascolto:
        elabora_audio()
        chiudi_frase_se_finita()

    # il server ha risposto e l'audio parte: la bocca inizia ad animarsi
    try:
        coda_volto.get_nowait()
        in_parlato = True
    except queue.Empty:
        pass

    # risultati dal thread di invio (si tocca la GUI solo da qui)
    try:
        esito, stato_ai = coda_esiti.get_nowait()
        ripristina(esito, stato_ai)
    except queue.Empty:
        pass

    aggiorna_volto()

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
finestra.geometry("960x540")
finestra.configure(bg=COLORE_SFONDO_VOLTO)

# volto di BMO: occupa tutta la finestra
carica_sprite()
volto = tk.Label(finestra, bg=COLORE_SFONDO_VOLTO, bd=0)
volto.place(relx=0.5, rely=0.5, anchor="center")

# riga di stato per il debug: nascosta, si mostra/nasconde con il tasto D
stato = tk.Label(
    finestra,
    text="Avvio microfono...",
    font=("Arial", 11, "bold"),
    fg="blue",
    bg=COLORE_SFONDO_VOLTO,
)

finestra.update_idletasks()
ridimensiona_sprite(finestra.winfo_screenwidth() if SCHERMO_INTERO else 960,
                    finestra.winfo_screenheight() if SCHERMO_INTERO else 540)
imposta_sprite(SPRITE_SPENTO)

finestra.bind("<Configure>", finestra_ridimensionata)
finestra.bind("<F11>", lambda e: schermo_intero(not finestra.attributes("-fullscreen")))
finestra.bind("<Escape>", lambda e: schermo_intero(False))
finestra.bind("<d>", lambda e: attiva_disattiva_debug())
finestra.bind("<Control-q>", lambda e: chiudi())

if SCHERMO_INTERO:
    schermo_intero(True)

finestra.protocol("WM_DELETE_WINDOW", chiudi)

aggiorna()

# avvio automatico del microfono
finestra.after(500, avvia_ascolto)

finestra.mainloop()
