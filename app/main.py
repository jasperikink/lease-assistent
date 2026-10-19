import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import agent

load_dotenv()

app = FastAPI(title="Lease-assistent")
log = logging.getLogger("uvicorn.error")

STATIC = Path(__file__).resolve().parent.parent / "static"


class Bericht(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    berichten: list[Bericht]


class ChatResponse(BaseModel):
    antwoord: str
    tools: list[str]
    controle: dict | None = None
    voertuig: dict | None = None


def controleer_wachtwoord(x_wachtwoord: str | None = Header(default=None)):
    wachtwoord = os.getenv("DEMO_WACHTWOORD")
    if wachtwoord and not secrets.compare_digest(x_wachtwoord or "", wachtwoord):
        raise HTTPException(status_code=401, detail="Onjuist wachtwoord.")


@app.post("/inloggen", status_code=204, dependencies=[Depends(controleer_wachtwoord)])
def inloggen():
    return None


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(controleer_wachtwoord)])
def chat(req: ChatRequest):
    if not req.berichten:
        raise HTTPException(status_code=400, detail="Geen berichten meegestuurd.")
    try:
        return agent.ask([b.model_dump() for b in req.berichten])
    except Exception as e:
        log.exception("Fout in de agent")
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
