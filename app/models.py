from datetime import date

from pydantic import BaseModel, Field


class Vehicle(BaseModel):
    kenteken: str
    merk: str
    model: str
    voertuigsoort: str
    eerste_toelating: date
    catalogusprijs: int | None = None


class LeaseRequest(BaseModel):
    aankoopprijs: float = Field(gt=0)
    aanbetaling: float = Field(default=0, ge=0)
    slottermijn_pct: float = Field(default=0, ge=0, le=1)
    looptijd_maanden: int
    kvk_maanden: int = Field(ge=0)


class AcceptanceResult(BaseModel):
    geaccepteerd: bool
    redenen: list[str]
