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

export type Voorbeeld = { afzender: string; tijd: string; tekst: string };

export type Herberekening = {
  kenteken: string;
  aankoopprijs: number;
  looptijd_maanden: number;
  aanbetaling: number;
  slottermijn_pct: number;
  kvk_maanden: number | null;
};

export type Bron = { document: string; sectie: string; tekst: string };

export type ChatResponse = {
  antwoord: string;
  tools: string[];
  controle: Controle | null;
  voertuig: Voertuig | null;
  bronnen: Bron[];
};

const SLEUTEL = "lease-assistent-wachtwoord";
const TELLER = "lease-assistent-vragen";

export const MAX_DEMO_VRAGEN = 5;

export function gesteldeVragen(): number {
  try {
    return Number(localStorage.getItem(TELLER)) || 0;
  } catch {
    return 0;
  }
}

export function telVraag(): number {
  const aantal = gesteldeVragen() + 1;
  try {
    localStorage.setItem(TELLER, String(aantal));
  } catch {
    return aantal;
  }
  return aantal;
}

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

async function verzoek(methode: "GET" | "POST", pad: string, wachtwoord: string, body?: unknown): Promise<Response> {
  const res = await fetch(pad, {
    method: methode,
    headers: { "Content-Type": "application/json", "x-wachtwoord": wachtwoord },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 401) {
    bewaarWachtwoord("");
    throw new NietIngelogd("Onjuist wachtwoord.");
  }
  return res;
}

async function json<T>(res: Response): Promise<T> {
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

export async function inloggen(wachtwoord: string) {
  const res = await verzoek("POST", "/inloggen", wachtwoord);
  if (!res.ok) throw new Error("Inloggen mislukt.");
  bewaarWachtwoord(wachtwoord);
}

export async function chat(berichten: Bericht[]): Promise<ChatResponse> {
  return json(await verzoek("POST", "/chat", opgeslagenWachtwoord(), { berichten }));
}

export async function voorbeelden(nieuw = false): Promise<Voorbeeld[]> {
  return json(await verzoek("GET", nieuw ? "/voorbeelden?nieuw=true" : "/voorbeelden", opgeslagenWachtwoord()));
}

export async function herbereken(invoer: Herberekening): Promise<Controle> {
  return json(await verzoek("POST", "/controle", opgeslagenWachtwoord(), invoer));
}

export const euro = (bedrag: number) =>
  new Intl.NumberFormat("nl-NL", { style: "currency", currency: "EUR" }).format(bedrag);
