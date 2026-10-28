# Progetto-AI-Robottino

### **Gruppo Skynet** <br>

### Obbiettivo: creare un piccolo compagno AI con cui interagire. <br>

Questo repository contiene il codice sorgente e la documentazione.
<br> <br>

| | Obbiettivi | Responsabile |
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

| | Idee Chiavi |
| :---: | :--- |
| ☑ | Parlare |
| ☑ | Traking visivo |
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
- **Parlare** (sintesi vocale, es. `pyttsx3`)
- **Riconoscimento suoni** (voce con `SpeechRecognition`/`PyAudio` e rumori)
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

## Installazione (Windows)

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

Il nome del modello deve coincidere con quello usato in `robot/brain.py`.

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

### Problemi comuni

| Errore | Soluzione |
| :--- | :--- |
| `ModuleNotFoundError: No module named 'speech_recognition'` | Il pacchetto si installa con `pip install SpeechRecognition` (nome diverso dall'import). |
| `Failed to connect to Ollama` | Ollama non è avviato: aprirlo dal menu Start o eseguire `ollama serve`. |
| `model not found` | Eseguire `ollama pull <nome-modello>` con lo stesso nome usato nel codice. |
| `No module named 'robot'` | Lanciare lo script dalla cartella principale (`python main.py`), non da una sottocartella. |
| Nessun microfono / errori ALSA | Capita solo su Linux o Codespace: il test della voce va fatto su Windows in locale. |

| Resources |  |
| :--- | :--- |
STT: | https://www.geeksforgeeks.org/python/python-convert-speech-to-text-and-text-to-speech/ |
LLM: | https://ollama.com/ |
 | |  https://developers.openai.com/api/docs/guides/text |
 | | https://developers.openai.com/api/reference/resources/chat |
 | |  https://platform.openai.com/tokenizer |
TTS: | https://pypi.org/project/TTS/ |
