# Mini-robot-AI

### Gruppo Skynet

**Obiettivo:** creare un piccolo compagno AI con cui interagire. Il robot **ascolta, risponde a voce e mostra un'espressione** in base allo stato emotivo della conversazione. È ispirato ad AIBI Pocket e al formato di BMO.

Il Raspberry Pi si occupa solo di microfono, altoparlante e display. Tutta la parte pesante (riconoscimento vocale, LLM, sintesi vocale) gira su un PC/portatile che espone una **API REST con FastAPI**.

Questo repository contiene il codice sorgente e la documentazione.

---

## Obiettivi del progetto

| | Obiettivo | Responsabile |
| :---: | :--- | :--- |
| ☑ | Chatbot da terminale | **Massimiliano** |
| ☐ | Progettare AI (personalità, umorismo, sentimenti) | **Massimiliano** |
| ☐ | Addestrare / affinare le risposte | **Massimiliano** |
| ☑ | Sviluppare i moduli (audio, visione, tocchi) | **Diego, Gabriele** |
| ☐ | Testing pc locale | **Tutti, ognuno sul proprio modulo** |
| ☐ | Integrare i moduli in un unico programma | **Massimiliano** |
| ☐ | Trovare componenti e fare la lista con i costi | **Tutti, ognuno per la propria area** |
| ☐ | Progettazione fisica (case, display) | **Niccolò** |
| ☐ | Implementazione fisica (assemblaggio) | **Niccolò, con tutti** |
| ☐ | Testing fisico | **Tutti** |

## Idee chiave

| | Idea |
| :---: | :--- |
| ☑ | Parlare |
| ☑ | Tracking visivo |
| ☐ | Riconoscimento suoni |
| ☐ | Riconoscimento tocchi |
| ☐ | Umorismo |
| ☐ | Sentimenti |

## Milestone

| | Milestone | Scadenza |
| :---: | :--- | :---: |
| ☐ | Base software pronta | 30/10 |
| ☐ | Documentazione conclusa | 6/11 |
| ☐ | Fine fase logica | 15/11 |
| ☐ | Fine fase fisica | 25/11 |
| ☐ | Consegna | 30/11 |

## Divisione del lavoro

### Massimiliano: AI e coordinamento
- Progettare l'AI (logica della conversazione, integrazione col modello Ollama)
- Addestrare / definire la personalità
- **Umorismo** e **Sentimenti**
- Gestione del repo e integrazione finale dei moduli
- Controllo compatibilità e budget della lista componenti

### Diego: audio
- **Parlare** (sintesi vocale)
- **Riconoscimento suoni** (voce e rumori)
- Testing pc locale della parte audio
- Componenti hardware audio: microfono, speaker, amplificatore

### Niccolò: progettazione fisica e design
- **Progettazione fisica**: case, dimensioni, disposizione dei componenti, stampa 3D
- Display e interfaccia / espressioni del viso
- **Implementazione fisica** (assemblaggio)
- Componenti: display, batteria, tasto accensione

### Gabriele: visione e sensori
- **Tracking visivo** (camera, riconoscimento volto/movimento, es. OpenCV + MediaPipe)
- **Riconoscimento tocchi** (sensori touch/capacitivi)
- Testing pc locale della parte visione/sensori
- Componenti: camera, sensori, microcontrollore

---

## Architettura

![Schema dell'architettura](docs/architettura.png)

Il sistema è diviso in tre blocchi:

| Blocco | Dispositivo | Responsabilità |
|---|---|---|
| **Raspberry IN** | Raspberry Pi | Resta in ascolto, registra la voce e produce un file `.wav` |
| **ClientServer** | PC / portatile | STT, generazione della risposta, TTS |
| **Raspberry OUT** | Raspberry Pi | Riproduce l'audio, mostra l'espressione, torna in ascolto |

Il Raspberry è lo stesso dispositivo nei due blocchi IN e OUT: sono separati nello schema solo per chiarezza.

### Flusso di funzionamento

1. **In ascolto**: il Raspberry attende la voce dell'utente.
2. **Registra la voce**: salva l'audio in un file `File .wav`.
3. **Invio via FastAPI**: il file viene inviato al server con una richiesta HTTP.
4. **STT** (*speech-to-text*): `faster-whisper` trascrive l'audio e produce un JSON con la **trascrizione**.
5. **Generazione risposta**: `qwen3.5:4b` (tramite Ollama) genera la risposta e restituisce un JSON con `role`, `content` e `state`.
6. **TTS** (*text-to-speech*): `piper` trasforma il testo in voce e produce `risposta .wav`. Il server restituisce anche il JSON `role, content, state`.
7. **Risposta via FastAPI**: audio e JSON tornano al Raspberry.
8. **Raspberry OUT**:
   - **Riproduce l'audio**: riproduce `risposta .wav`;
   - **Visualizza l'espressione**: usa il campo `state` del JSON per scegliere l'espressione da mostrare.
9. **Finisce di rispondere**: terminata la risposta, il robot torna al punto 1.

### Componenti e tecnologie

| Funzione | Strumento |
|---|---|
| API tra Raspberry e server | FastAPI |
| Riconoscimento vocale (STT) | faster-whisper |
| Modello linguistico (LLM) | qwen3.5:4b, eseguito con Ollama |
| Sintesi vocale (TTS) | Piper |
| Formato dei messaggi | JSON |
| Audio scambiato | file `.wav` |

### Perché un server separato

I Raspberry a disposizione non sono abbastanza potenti per eseguire in locale LLM, STT e TTS. Per questo il robot invia l'audio a un PC/portatile tramite l'API REST e riceve indietro la risposta già pronta.

---

## Formato dei dati

### Dopo l'STT: trascrizione

Contiene il testo riconosciuto dall'audio dell'utente.

### Dopo l'LLM: risposta con stato

```json
{
  "role": "assistant",
  "content": "Ciao! Sono contento di vederti.",
  "state": "happy"
}
```

| Campo | Significato |
|---|---|
| `role` | Chi parla (es. `assistant`) |
| `content` | Testo della risposta, letto dal TTS |
| `state` | Stato emotivo scelto dall'LLM in base alla conversazione (es. `happy`, `angry`, `idle`) |

Lo `state` non viene pronunciato: serve al Raspberry per decidere quale espressione visualizzare.

## Gli stati del robot

L'LLM assegna a sé stesso uno stato in base all'andamento della conversazione. Esempi: `happy`, `angry`, `idle`. A ogni stato corrisponde un'espressione sul display del Raspberry.

## Branch

Il branch `Status` è quello in cui viene aggiunta la gestione degli **stati** (`state`) alla risposta dell'LLM.

---

## Installazione (Windows)

> Queste istruzioni riguardano la **fase locale su PC** (test dei moduli sul proprio computer). Nell'architettura con server FastAPI, STT, LLM e TTS sono quelli indicati nella sezione Architettura (faster-whisper, qwen3.5:4b, Piper).

I comandi vanno eseguiti in **PowerShell** o nel **Prompt dei comandi**.

### 1. Prerequisiti (una volta sola)

Servono Python, Git e Ollama. Si possono installare dai siti ufficiali (python.org, git-scm.com, ollama.com/download) oppure con `winget`:

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id Git.Git
winget install -e --id Ollama.Ollama
```

> Se Python si installa dal sito, spuntare **"Add Python to PATH"**.
> Si consiglia Python 3.12 o 3.13: con versioni troppo recenti PyAudio potrebbe non avere ancora i pacchetti precompilati.

Dopo l'installazione **chiudere e riaprire il terminale**.

### 2. Clonare il progetto

```powershell
git clone <url-del-repo>
cd Mini-robot-AI
```

### 3. Ambiente virtuale e dipendenze

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install pyttsx3 SpeechRecognition pyaudio ollama
```

Se PowerShell blocca l'attivazione del venv, eseguire una volta:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Se `pip install pyaudio` fallisce:

```powershell
pip install pipwin
pipwin install pyaudio
```

### 4. Scaricare il modello Ollama

```powershell
ollama pull llama3.2
ollama list
```

Il nome del modello deve coincidere con quello usato in `robot/brain.py`. Per il modello del branch `Status` si usa `ollama pull qwen3.5:4b`.

Per verificare che Ollama sia attivo:

```powershell
curl http://localhost:11434
```

Deve rispondere `Ollama is running`. Se non risponde, avviarlo dal menu Start oppure con:

```powershell
ollama serve
```

### 5. Avvio

Sempre dalla cartella principale del progetto, con il venv attivo (nel prompt deve comparire `(.venv)`):

```powershell
python main.py
```

### Installazione voci (Piper)

```powershell
pip install piper-tts
python -m piper.download_voices it_IT-serena-high
```

### Problemi comuni

| Errore | Soluzione |
| :--- | :--- |
| `ModuleNotFoundError: No module named 'speech_recognition'` | Il pacchetto si installa con `pip install SpeechRecognition` (nome diverso dall'import). |
| `Failed to connect to Ollama` | Ollama non è avviato: aprirlo dal menu Start o eseguire `ollama serve`. |
| `model not found` | Eseguire `ollama pull <nome-modello>` con lo stesso nome usato nel codice. |
| `No module named 'robot'` | Lanciare lo script dalla cartella principale (`python main.py`), non da una sottocartella. |
| Nessun microfono / errori ALSA | Capita solo su Linux o Codespace: il test della voce va fatto su Windows in locale. |

---

## Risorse

| Area | Link |
| :--- | :--- |
| STT | https://www.geeksforgeeks.org/python/python-convert-speech-to-text-and-text-to-speech/ |
| LLM | https://ollama.com/ |
| LLM | https://developers.openai.com/api/docs/guides/text |
| LLM | https://developers.openai.com/api/reference/resources/chat |
| LLM | https://platform.openai.com/tokenizer |
| TTS | https://pypi.org/project/TTS/ |

---

## Da completare

- struttura delle cartelle e descrizione dei file
- endpoint FastAPI (percorsi, parametri, esempi di richiesta e risposta)
- avvio del server FastAPI e del client sul Raspberry
- elenco completo degli stati e delle espressioni associate
