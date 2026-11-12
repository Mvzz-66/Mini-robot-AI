# main.py
# Punto di ingresso del robot: ascolta una domanda a voce (o da tastiera se
# non c'è il microfono), la passa al "cervello" e fa rispondere il robot.
# Il ciclo continua finché l'utente non dice "esci".


import os
import secrets
import tempfile

from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.responses import FileResponse, Response
from starlette.background import BackgroundTask

from input.voice import Voice
from robot import brain

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("BMO_API_KEY")
if not API_KEY:
    raise RuntimeError("Imposta la variabile d'ambiente BMO_API_KEY")

app = FastAPI()
voice = Voice()


def check_key(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="API key non valida")


@app.post("/talk", dependencies=[Depends(check_key)])
def talk(file: UploadFile = File(...)):
    # 1. salva il wav ricevuto
    fd, in_path = tempfile.mkstemp(suffix=".wav")
    with os.fdopen(fd, "wb") as f:
        f.write(file.file.read())

    # 2. STT
    try:
        domanda = voice.voiceRec(in_path)
    finally:
        os.remove(in_path)

    print("Tu:", domanda)
    if not domanda:
        return Response(status_code=204)  # nessun parlato rilevato

    # 3. LLM
    risposta = brain.rispondi(domanda)
    print("BMO:", risposta)

    # 4. TTS e invio del wav (poi viene cancellato)
    out_path = voice.synthesize(risposta)
    return FileResponse(
        out_path,
        media_type="audio/wav",
        background=BackgroundTask(os.remove, out_path),
    ) 