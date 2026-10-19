import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import agent, limieten, voorbeelden

load_dotenv()

app = FastAPI(title="Lease-assistent")
log = logging.getLogger("uvicorn.error")

STATIC = Path(__file__).resolve().parent.parent / "static"


class Bericht(BaseModel):
    role: str
    content: str = Field(max_length=limieten.MAX_TEKENS_PER_BERICHT)


class ChatRequest(BaseModel):
    berichten: list[Bericht] = Field(max_length=20)


class ChatResponse(BaseModel):
    antwoord: str
    tools: list[str]
    controle: dict | None = None
    voertuig: dict | None = None
    bronnen: list[dict] = []


class ControleRequest(BaseModel):
    kenteken: str
    aankoopprijs: float
    looptijd_maanden: int
    aanbetaling: float = 0
    slottermijn_pct: float = 0
    kvk_maanden: int | None = None


def controleer_wachtwoord(x_wachtwoord: str | None = Header(default=None)):
    wachtwoord = os.getenv("DEMO_WACHTWOORD")
    if wachtwoord and not secrets.compare_digest(x_wachtwoord or "", wachtwoord):
        raise HTTPException(status_code=401, detail="Onjuist wachtwoord.")


@app.post("/inloggen", status_code=204, dependencies=[Depends(controleer_wachtwoord)])
def inloggen():
    return None


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(controleer_wachtwoord)])
def chat(req: ChatRequest, request: Request):
    if not req.berichten:
        raise HTTPException(status_code=400, detail="Geen berichten meegestuurd.")
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "onbekend")
    if not limieten.binnen_limiet(ip.split(",")[0].strip()):
        raise HTTPException(status_code=429, detail="Je hebt het maximum aantal vragen voor dit uur bereikt.")
    try:
        return agent.ask(limieten.kort_in([b.model_dump() for b in req.berichten]))
    except Exception as e:
        log.exception("Fout in de agent")
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")


@app.get("/voorbeelden", dependencies=[Depends(controleer_wachtwoord)])
def lijst_voorbeelden(nieuw: bool = False) -> list[dict]:
    return voorbeelden.maak_voorbeelden(nieuw)


@app.post("/controle", dependencies=[Depends(controleer_wachtwoord)])
def controle(req: ControleRequest) -> dict:
    resultaat = agent.controleer_lease.invoke(req.model_dump())
    if "fout" in resultaat:
        raise HTTPException(status_code=422, detail=resultaat["fout"])
    return resultaat


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
