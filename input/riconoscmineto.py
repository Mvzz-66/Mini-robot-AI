import threading
import time
import unicodedata

import cv2
import dlib
import ollama

MODELLO = "qwen3-vl:2b-instruct"   # più veloce: "qwen3-vl:2b-instruct"
PROMPT = "Describe this person's face in max 6 words (expression, glasses, hair)."
INTERVALLO = 5      # secondi minimi tra una richiesta e l'altra
SCALA = 0.5         # riduzione del frame per dlib (più basso = più fps)

etichetta = ""
in_corso = False
ultima_richiesta = 0            


def pulisci(testo):
    """putText non disegna le lettere accentate: le converto in ASCII."""
    t = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    return t.strip().split("\n")[0][:40]


def scalda_modello():
    """Carica il modello in RAM all'avvio, così la prima risposta vera è veloce."""
    try:
        ollama.chat(model=MODELLO, messages=[{"role": "user", "content": "hi"}],
                    options={"num_predict": 1}, keep_alive="30m")
    except Exception as e:
        print("Riscaldamento modello fallito:", e)


def chiedi_ai(crop):
    global etichetta, in_corso
    t0 = time.time()
    try:
        crop = cv2.resize(crop, (256, 256))    # meno pixel = molto più veloce
        _, buf = cv2.imencode(".jpg", crop)
        r = ollama.chat(
            model=MODELLO,
            messages=[{"role": "user", "content": PROMPT,
                       "images": [buf.tobytes()]}],
            options={"num_predict": 25, "temperature": 0},
            keep_alive="30m",
        )
        testo = r["message"]["content"]
        etichetta = pulisci(testo) or "(risposta vuota)"
        print(f"{time.time() - t0:.1f}s -> {testo!r}")
    except Exception as e:
        etichetta = "errore AI"
        print(e)
    finally:
        in_corso = False


# ---------- AVVIO ----------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Webcam non trovata")

detector = dlib.get_frontal_face_detector()
threading.Thread(target=scalda_modello, daemon=True).start()

# ---------- CICLO PRINCIPALE ----------
while True:
    ret, img = cap.read()
    if not ret:
        break
    img = cv2.flip(img, 1)  # specchio

    # detection su immagine ridotta
    piccola = cv2.resize(img, None, fx=SCALA, fy=SCALA)
    rgb = cv2.cvtColor(piccola, cv2.COLOR_BGR2RGB)
    detected = detector(rgb, 0)

    for d in detected:
        # coordinate riportate alla dimensione originale
        x1 = max(int(d.left() / SCALA), 0)
        y1 = max(int(d.top() / SCALA), 0)
        x2 = int((d.right() + 1) / SCALA)
        y2 = int((d.bottom() + 1) / SCALA)

        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
        testo = etichetta or ("analizzo..." if in_corso else "")
        cv2.putText(img, testo, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # chiedo all'AI solo se è libera e sono passati abbastanza secondi
        crop = img[y1:y2, x1:x2]
        if (not in_corso and crop.size > 0
                and time.time() - ultima_richiesta > INTERVALLO):
            in_corso = True
            ultima_richiesta = time.time()
            threading.Thread(target=chiedi_ai, args=(crop.copy(),),
                             daemon=True).start()
        break  # solo il primo volto

    cv2.imshow("result", img)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
