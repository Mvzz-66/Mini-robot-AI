# main.py
# Punto di ingresso del robot: ascolta una domanda a voce (o da tastiera se
# non c'è il microfono), la passa al "cervello" e fa rispondere il robot.
# Il ciclo continua finché l'utente non dice "esci".


from input.voice import Voice
from fastapi import FastAPI

app = FastAPI()

    