# Avvio del server API di BMO (Linux e Windows)

Il server (`server.py`, FastAPI) riceve un file audio `.wav` su `/talk`, lo trascrive (Whisper), lo passa al cervello (Ollama) e risponde con un `.wav` generato da Piper.

Ogni comando che cambia tra sistemi è dato in due versioni: **Linux (Arch, bash)** e **Windows (PowerShell)**. Dove serve c'è anche la variante CMD.

## Requisiti

- Python 3.12 (venv in `.venv`, creato con `uv`)
- Ollama in esecuzione con il modello indicato in `robot/config.py` (es. `qwen3.5:4b`)
- Modello Piper `.onnx` indicato in `config.py`

Verifica Ollama e modello:

**Linux**
```bash
systemctl status ollama
ollama list
```

**Windows**
```powershell
ollama list
```
Su Windows Ollama parte come app in background (icona nella barra delle applicazioni). Se `ollama list` non risponde, avvia l'app Ollama dal menu Start.

> Se `ollama serve` dà `address already in use` (Linux) o un errore sulla porta 11434 (Windows), Ollama è già attivo: non va riavviato.

## Creazione del venv e installazione dipendenze

Il venv è creato con `uv` e non contiene `pip`: si usa `uv pip`.

Installa `uv` se manca:

**Linux**
```bash
sudo pacman -S uv
```

**Windows**
```powershell
winget install astral-sh.uv
```
(in alternativa: `python -m pip install uv`)

Crea il venv con Python 3.12 (solo la prima volta):

**Linux**
```bash
cd ~/Documents/IA/Mini-robot-AI
uv venv --python 3.12 .venv
```

**Windows**
```powershell
cd C:\percorso\del\progetto\Mini-robot-AI
uv venv --python 3.12 .venv
```

Attiva il venv e installa le librerie:

**Linux**
```bash
source .venv/bin/activate

uv pip install fastapi uvicorn python-multipart opencv-python dlib ollama \
  sounddevice soundfile faster-whisper piper-tts "av<17"
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1

uv pip install fastapi uvicorn python-multipart opencv-python dlib ollama `
  sounddevice soundfile faster-whisper piper-tts "av<17"
```

**Windows (CMD)**
```cmd
.venv\Scripts\activate.bat

uv pip install fastapi uvicorn python-multipart opencv-python dlib ollama ^
  sounddevice soundfile faster-whisper piper-tts "av<17"
```

> Se PowerShell blocca lo script di attivazione (`running scripts is disabled`), esegui una volta:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

> `av<17` è necessario: con `av` 19 `faster-whisper` dà l'errore `unexpected keyword argument 'metadata_errors'`.

### Note sulle librerie

- **`dlib`** richiede compilazione. Su Linux: `sudo pacman -S cmake base-devel`. Su Windows servono i *Build Tools di Visual Studio* (carico di lavoro "Sviluppo di applicazioni desktop con C++") e CMake; in alternativa prova `uv pip install dlib-bin`.
- **`sounddevice`** su Linux richiede PortAudio (`sudo pacman -S portaudio`); su Windows è incluso nel pacchetto.
- **`soundfile`** su Linux richiede `libsndfile` (`sudo pacman -S libsndfile`); su Windows è incluso nel pacchetto.

## Chiave API (`BMO_API_KEY`)

La chiave non si ottiene da nessun servizio: la scegli tu. Il server la legge **una sola volta, all'avvio**, dalla variabile d'ambiente.

Genera una chiave casuale (stesso comando su entrambi i sistemi):

```
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Avvio del server

Nello **stesso terminale** imposta la chiave e avvia uvicorn.

**Linux**
```bash
source .venv/bin/activate
export BMO_API_KEY="la_tua_chiave"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
$env:BMO_API_KEY = "la_tua_chiave"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

**Windows (CMD)**
```cmd
.venv\Scripts\activate.bat
set BMO_API_KEY=la_tua_chiave
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

- `server:app` = file `server.py`, variabile `app = FastAPI()`. Va lanciato dalla cartella del progetto.
- `--host 0.0.0.0` rende il server raggiungibile dalla rete locale (serve per il robot). Per usarlo solo sul PC, usa `--host 127.0.0.1`.
- Durante lo sviluppo si può aggiungere `--reload`, ma i modelli vengono ricaricati a ogni modifica.
- Se cambi `BMO_API_KEY` o il codice (senza `--reload`), riavvia il server.

### Chiave permanente (opzionale)

**Linux:** aggiungi `export BMO_API_KEY="la_tua_chiave"` a `~/.bashrc` (o `~/.zshrc`).

**Windows:**
```powershell
setx BMO_API_KEY "la_tua_chiave"
```
Dopo `setx` apri un **nuovo** terminale: quello già aperto non vede il valore.

### Firewall su Windows

Con `--host 0.0.0.0`, alla prima esecuzione Windows può chiedere di consentire Python nel firewall: accetta solo per le **reti private**. Se il robot non riesce a connettersi, controlla che la porta 8000 sia consentita.

## Test

### Da Swagger

Apri http://127.0.0.1:8000/docs, scegli `POST /talk`, inserisci la chiave in `x-api-key`, carica un `.wav` e premi **Execute**.

### Da terminale

**Linux**
```bash
curl --fail -X POST http://127.0.0.1:8000/talk \
  -H "x-api-key: la_tua_chiave" \
  -F "file=@speech.wav" \
  --output risposta.wav

aplay risposta.wav
```

**Windows (PowerShell)**

In PowerShell `curl` è un alias di `Invoke-WebRequest`: usa **`curl.exe`**.

```powershell
curl.exe --fail -X POST http://127.0.0.1:8000/talk `
  -H "x-api-key: la_tua_chiave" `
  -F "file=@speech.wav" `
  --output risposta.wav

(New-Object Media.SoundPlayer "risposta.wav").PlaySync()
```

**Windows (CMD)**
```cmd
curl --fail -X POST http://127.0.0.1:8000/talk ^
  -H "x-api-key: la_tua_chiave" ^
  -F "file=@speech.wav" ^
  --output risposta.wav

start risposta.wav
```

`--fail` evita di salvare un messaggio di errore dentro `risposta.wav`.

## Codici di risposta

| Codice | Significato |
|---|---|
| 200 | Tutto ok, il corpo è il wav di risposta |
| 204 | Nessun parlato rilevato nel wav |
| 401 | `x-api-key` diversa da `BMO_API_KEY` usata all'avvio |
| 405 | Un `GET` su `/talk` (di solito il browser): `/talk` accetta solo `POST`, si ignora |
| 500 | Errore interno: il traceback è nel terminale di uvicorn |

## Risoluzione problemi

- **401 / `API key non valida`**: la chiave del client non coincide con quella del server. Riavvia uvicorn nel terminale in cui hai impostato la variabile, oppure incolla la chiave a mano nel comando.
- **`risposta.wav` non si riproduce**: guarda cosa contiene. Se è testo (es. `{"detail":"API key non valida"}`), è un errore e non audio.
  - Linux: `cat risposta.wav`
  - Windows (PowerShell): `Get-Content risposta.wav`
  - Windows (CMD): `type risposta.wav`
- **500**: testa i tre pezzi uno alla volta (i comandi sono uguali su Linux e Windows):
  - STT: `python -c "from input.voice import Voice; v=Voice(); print(v.voiceRec('speech.wav'))"`
  - LLM: `python -c "from robot import brain; print(brain.rispondi('ciao'))"`
  - TTS: `python -c "from input.voice import Voice; v=Voice(); print(v.synthesize('ciao'))"`
- **Modello `.onnx` di pochi byte**: se è gestito con Git LFS esegui `git lfs pull`.
- **`No module named pip`**: usa `uv pip install ...` invece di `pip`.
- **Porta 8000 già occupata**:
  - Linux: `ss -ltnp | grep 8000`
  - Windows: `netstat -ano | findstr :8000` (l'ultima colonna è il PID; chiudi il processo da Gestione attività) oppure usa un'altra porta con `--port 8001`.
- **`uvicorn` non trovato**: usa sempre `python -m uvicorn ...` con il venv attivo.

## Sicurezza

- Non scrivere la chiave nel codice e non committarla su Git. Se la metti in un file `.env`, aggiungilo a `.gitignore`.
- La chiave protegge l'accesso, ma il traffico è in HTTP semplice: va bene in rete locale, non esporre il server su internet senza HTTPS.
- Se una chiave è finita in uno screenshot o su un repository pubblico, generane una nuova.
