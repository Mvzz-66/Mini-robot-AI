# Progetto-AI-Robottino

### **Gruppo Skynet** <br>

### Obbiettivo: creare un piccolo compagno AI con cui chiacchierare. <br>

Questo repository contiene il codice sorgente e la documentazione.
<br> <br>

| Ruolo | Nome | Responsabilità |
| :--- | :--- | :--- |
Capo Gruppo:  |   **Massimiliano Drago** | *Sviluppatore Software/Hardware* | 
Componente 1:     |   **Diego Scatizzi** | *Sviluppatore Software/Hardware* |
Componente 2:     |   **Niccolò Sbragi** | *Sviluppatore Software/Hardware e Designer* |
Componente 2:     |   **Gabriele Severi** | *Sviluppatore Software/Hardware* |

| | Obbiettivi | Responsabile |
| :---: | :--- | :--- |
| ☑ | Chatbot da terminale | Massimiliano |
| ☐ | Progettare AI (personalità, umorismo, sentimenti) | Massimiliano |
| ☐ | Addestrare / affinare le risposte | Massimiliano |
| ☐ | Sviluppare i moduli (audio, visione, tocchi) | Diego, Gabriele |
| ☐ | Testing pc locale | Tutti, ognuno sul proprio modulo |
| ☐ | Integrare i moduli in un unico programma | Massimiliano |
| ☐ | Trovare componenti e fare la lista con i costi | Tutti, ognuno per la propria area |
| ☐ | Progettazione fisica (case, display) | Niccolò |
| ☐ | Implementazione fisica (assemblaggio) | Niccolò, con tutti |
| ☐ | Testing fisico | Tutti |

| | Idee Chiavi |
| :---: | :--- |
| ☐ | Parlare |
| ☐ | Traking visivo |
| ☐ | Riconoscimento suoni |
| ☐ | Riconoscimento tocchi |
| ☐ | Umorismo |
| ☐ | Sentimenti |

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


| Resources |  |
| :--- | :--- |
STT: | https://www.geeksforgeeks.org/python/python-convert-speech-to-text-and-text-to-speech/ |
LLM: | https://ollama.com/ |
 | |  https://developers.openai.com/api/docs/guides/text |
 | | https://developers.openai.com/api/reference/resources/chat |
 | |  https://platform.openai.com/tokenizer |
TTS: | https://pypi.org/project/TTS/ |


  
