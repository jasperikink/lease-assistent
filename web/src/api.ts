export type Voertuig = {
  kenteken: string;
  merk: string;
  model: string;
  voertuigsoort: string;
  eerste_toelating: string;
};

export type Invoer = {
  aankoopprijs: number;
  aanbetaling: number;
  slottermijn_pct: number;
  looptijd_maanden: number;
  kvk_maanden: number | null;
  kvk_sinds: string | null;
};

export type Controle = {
  voertuig: Voertuig;
  invoer: Invoer;
  geaccepteerd: boolean;
  redenen: string[];
  rente_pct: number;
  maandbedrag: number | null;
  slottermijn_eind: number;
  let_op?: string;
};

export type Bericht = { role: "user" | "assistant"; content: string };

export type ChatResponse = {
  antwoord: string;
  tools: string[];
  controle: Controle | null;
  voertuig: Voertuig | null;
};

const SLEUTEL = "lease-assistent-wachtwoord";

export class NietIngelogd extends Error {}

export function opgeslagenWachtwoord(): string {
  try {
    return sessionStorage.getItem(SLEUTEL) ?? "";
  } catch {
    return "";
  }
}

function bewaarWachtwoord(wachtwoord: string) {
  try {
    if (wachtwoord) sessionStorage.setItem(SLEUTEL, wachtwoord);
    else sessionStorage.removeItem(SLEUTEL);
  } catch {
    return;
  }
}

async function post(pad: string, wachtwoord: string, body?: unknown): Promise<Response> {
  const res = await fetch(pad, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-wachtwoord": wachtwoord },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 401) {
    bewaarWachtwoord("");
    throw new NietIngelogd("Onjuist wachtwoord.");
  }
  return res;
}

export async function inloggen(wachtwoord: string) {
  await post("/inloggen", wachtwoord);
  bewaarWachtwoord(wachtwoord);
}

export async function chat(berichten: Bericht[]): Promise<ChatResponse> {
  const res = await post("/chat", opgeslagenWachtwoord(), { berichten });
  const tekst = await res.text();
  if (!res.ok) {
    let detail = tekst;
    try {
      detail = JSON.parse(tekst).detail ?? tekst;
    } catch {
      detail = tekst;
    }
    throw new Error(detail);
  }
  return JSON.parse(tekst);
}

export const euro = (bedrag: number) =>
  new Intl.NumberFormat("nl-NL", { style: "currency", currency: "EUR" }).format(bedrag);
