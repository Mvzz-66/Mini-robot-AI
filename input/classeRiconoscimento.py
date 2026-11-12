import threading
import time
import unicodedata
import cv2
import dlib
import ollama

class AnalizzatoreVoltoAI:
    def __init__(self, modello="qwen3-vl:2b-instruct", intervallo=5, scala=0.5):
        # Configurazione parametri
        self.modello = modello
        self.prompt = "Describe this person's face in max 6 words (expression, glasses, hair)."
        self.intervallo = intervallo
        self.scala = scala

        # Stato interno della classe
        self.etichetta = ""
        self.in_corso = False
        self.ultima_richiesta = 0            

        # Inizializzazione strumenti
        self.detector = dlib.get_frontal_face_detector()
        
        # Avvia il riscaldamento del modello in background all'istanza
        threading.Thread(target=self._scalda_modello, daemon=True).start()

    def _pulisci(self, testo):
        """Converte le lettere accentate in ASCII per cv2.putText."""
        t = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
        return t.strip().split("\n")[0][:40]

    def _scalda_modello(self):
        """Carica il modello in RAM all'avvio."""
        try:
            ollama.chat(
                model=self.modello, 
                messages=[{"role": "user", "content": "hi"}],
                options={"num_predict": 1}, 
                keep_alive="30m"
            )
        except Exception as e:
            print("Riscaldamento modello fallito:", e)

    def _chiedi_ai(self, crop):
        """Invia il ritaglio del volto alle API Ollama."""
        t0 = time.time()
        try:
            crop = cv2.resize(crop, (256, 256))  # Ridimensiona per ottimizzare la velocità
            _, buf = cv2.imencode(".jpg", crop)
            r = ollama.chat(
                model=self.modello,
                messages=[{"role": "user", "content": self.prompt, "images": [buf.tobytes()]}],
                options={"num_predict": 25, "temperature": 0},
                keep_alive="30m",
            )
            testo = r["message"]["content"]
            self.etichetta = self._pulisci(testo) or "(risposta vuota)"
            print(f"{time.time() - t0:.1f}s -> {testo!r}")
        except Exception as e:
            self.etichetta = "errore AI"
            print(e)
        finally:
            self.in_corso = False

    def avvia(self, sorgente_video=0):
        """Avvia il ciclo principale di acquisizione ed elaborazione video."""
        cap = cv2.VideoCapture(sorgente_video)
        if not cap.isOpened():
            raise SystemExit("Webcam non trovata")

        try:
            while True:
                ret, img = cap.read()
                if not ret:
                    break
                img = cv2.flip(img, 1)  # Effetto specchio

                # Detection su immagine ridotta per massimizzare gli FPS
                piccola = cv2.resize(img, None, fx=self.scala, fy=self.scala)
                rgb = cv2.cvtColor(piccola, cv2.COLOR_BGR2RGB)
                detected = self.detector(rgb, 0)

                for d in detected:
                    # Riproporziona le coordinate alla dimensione reale dell'immagine
                    x1 = max(int(d.left() / self.scala), 0)
                    y1 = max(int(d.top() / self.scala), 0)
                    x2 = int((d.right() + 1) / self.scala)
                    y2 = int((d.bottom() + 1) / self.scala)

                    # Disegna rettangolo e testo
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    testo_output = self.etichetta or ("analizzo..." if self.in_corso else "")
                    cv2.putText(img, testo_output, (x1, max(y1 - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                    # Esegue la richiesta asincrona all'AI se le condizioni sono rispettate
                    crop = img[y1:y2, x1:x2]
                    ora_attuale = time.time()
                    if (not self.in_corso and crop.size > 0
                            and ora_attuale - self.ultima_richiesta > self.intervallo):
                        self.in_corso = True
                        self.ultima_richiesta = ora_attuale
                        threading.Thread(target=self._chiedi_ai, args=(crop.copy(),), daemon=True).start()
                    break  # Elabora solo il primo volto trovato

                cv2.imshow("Analisi Volto AI", img)
                if cv2.waitKey(1) == 27:  # Tasto ESC per uscire
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

# ---------- ESECUZIONE ----------
if __name__ == "__main__":
    # Puoi personalizzare i parametri passando argomenti come: AnalizzatoreVoltoAI(intervallo=3)
    app = AnalizzatoreVoltoAI()
    app.avvia()
