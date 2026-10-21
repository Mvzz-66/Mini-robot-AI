# Progetto-AI-Robottino

### **Gruppo Skynet** <br>

### Obbiettivo: creare un piccolo compagno AI con cui chiacchierare. <br>

Questo repository contiene il codice sorgente e la documentazione..
<br> <br>

| Ruolo | Nome | Responsabilità |
| :--- | :--- | :--- |
Capo Gruppo:  |   **Massimiliano Drago** | *Sviluppatore Software/Hardware* <br> 
Componente 1:     |   **Diego Scatizzi** | *Sviluppatore Software/Hardware* <br>
Componente 2:     |   **Niccolò Sbragi** | *Sviluppatore Software/Hardware e Designer* <br>
Componente 2:     |   **Gabriele Severi** | *Sviluppatore Software/Hardware* <br>

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