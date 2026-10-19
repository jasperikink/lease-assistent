import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import {
  Bericht,
  Bron,
  Controle,
  Herberekening,
  MAX_DEMO_VRAGEN,
  NietIngelogd,
  Voertuig,
  Voorbeeld,
  chat,
  gesteldeVragen,
  herbereken,
  opgeslagenWachtwoord,
  telVraag,
  voorbeelden,
} from "./api";
import { Antwoord } from "./components/Antwoord";
import { Dossier } from "./components/Dossier";
import { Inbox } from "./components/Inbox";
import { Inloggen } from "./components/Inloggen";

type Beurt =
  | { soort: "vraag"; tekst: string }
  | { soort: "antwoord"; tekst: string; tools: string[]; bronnen: Bron[] }
  | { soort: "fout"; tekst: string };

export function App() {
  const [ingelogd, setIngelogd] = useState(() => opgeslagenWachtwoord() !== "");
  const [beurten, setBeurten] = useState<Beurt[]>([]);
  const [invoer, setInvoer] = useState("");
  const [bezig, setBezig] = useState(false);
  const [controle, setControle] = useState<Controle | null>(null);
  const [voertuig, setVoertuig] = useState<Voertuig | null>(null);
  const [herberekend, setHerberekend] = useState(false);
  const [inbox, setInbox] = useState<Voorbeeld[] | null>(null);
  const [inboxFout, setInboxFout] = useState(false);
  const [vernieuwen, setVernieuwen] = useState(false);
  const [gesteld, setGesteld] = useState(gesteldeVragen);
  const op = gesteld >= MAX_DEMO_VRAGEN;
  const einde = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ingelogd) laadInbox();
  }, [ingelogd]);

  useEffect(() => {
    einde.current?.scrollIntoView({ behavior: "smooth" });
  }, [beurten, bezig]);

  async function laadInbox(nieuw = false) {
    if (!nieuw) setInbox(null);
    setInboxFout(false);
    setVernieuwen(true);
    try {
      setInbox(await voorbeelden(nieuw));
    } catch (e) {
      if (e instanceof NietIngelogd) setIngelogd(false);
      else setInboxFout(true);
    } finally {
      setVernieuwen(false);
    }
  }

  function terug() {
    setBeurten([]);
    setControle(null);
    setVoertuig(null);
    setHerberekend(false);
  }

  async function onHerbereken(invoer: Herberekening): Promise<Controle> {
    try {
      const nieuw = await herbereken(invoer);
      setControle(nieuw);
      setHerberekend(true);
      return nieuw;
    } catch (e) {
      if (e instanceof NietIngelogd) setIngelogd(false);
      throw e;
    }
  }

  async function verstuur(tekst: string) {
    const vraag = tekst.trim();
    if (!vraag || bezig || op) return;

    const geschiedenis: Bericht[] = beurten.flatMap((b): Bericht[] =>
      b.soort === "vraag" ? [{ role: "user", content: b.tekst }]
      : b.soort === "antwoord" ? [{ role: "assistant", content: b.tekst }]
      : [],
    );

    setBeurten((huidig) => [...huidig, { soort: "vraag", tekst: vraag }]);
    setInvoer("");
    setBezig(true);
    try {
      const res = await chat([...geschiedenis, { role: "user", content: vraag }]);
      setBeurten((huidig) => [...huidig, { soort: "antwoord", tekst: res.antwoord, tools: res.tools, bronnen: res.bronnen }]);
      setGesteld(telVraag());
      if (res.controle) {
        setControle(res.controle);
        setHerberekend(false);
      }
      if (res.voertuig) setVoertuig(res.voertuig);
    } catch (e) {
      if (e instanceof NietIngelogd) {
        setIngelogd(false);
        return;
      }
      const melding = e instanceof Error ? e.message : "Onbekende fout";
      setBeurten((huidig) => [...huidig, { soort: "fout", tekst: melding }]);
    } finally {
      setBezig(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    verstuur(invoer);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      verstuur(invoer);
    }
  }

  if (!ingelogd) return <Inloggen onIngelogd={() => setIngelogd(true)} />;

  return (
    <div className="app">
      <header className="kop">
        <h1>Lease-assistent</h1>
        <p>Plak het bericht van de klant. Kenteken, beleid en maandbedrag worden voor je nagelopen.</p>
      </header>

      <main className="werkblad">
        <section className="gesprek" aria-live="polite">
          {beurten.length === 0 ? (
            <Inbox berichten={inbox} fout={inboxFout} bezig={vernieuwen} uitgeschakeld={op} onKies={verstuur} onVernieuw={() => laadInbox(true)} />
          ) : (
            <button type="button" className="terug" onClick={terug} disabled={bezig}>
              Terug naar de berichten
            </button>
          )}

          {beurten.map((b, i) =>
            b.soort === "vraag" ? (
              <div key={i} className="vraag">{b.tekst}</div>
            ) : b.soort === "antwoord" ? (
              <Antwoord key={i} tekst={b.tekst} tools={b.tools} bronnen={b.bronnen} />
            ) : (
              <div key={i} className="fout">{b.tekst}</div>
            ),
          )}

          {bezig && <div className="bezig">Kenteken opzoeken en beleid nalopen</div>}
          <div ref={einde} />
        </section>

        <Dossier controle={controle} voertuig={voertuig} herberekend={herberekend} onHerbereken={onHerbereken} />
      </main>

      <form className="invoer" onSubmit={onSubmit}>
        <div className="invoer-binnen">
          <label htmlFor="bericht" className="sr-only">Bericht van de klant</label>
          <div className="invoer-rij">
            <textarea
              id="bericht"
              value={invoer}
              onChange={(e) => setInvoer(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={op ? "De demovragen zijn op" : "Plak hier het bericht van de klant"}
              rows={2}
              maxLength={1500}
              disabled={op}
            />
            <button type="submit" disabled={bezig || op || !invoer.trim()}>
              Controleer
            </button>
          </div>
          <p className="teller">
            {op
              ? `Je hebt de ${MAX_DEMO_VRAGEN} vragen van deze demo gebruikt. Herberekenen in het dossier kan nog wel, dat gebruikt geen AI.`
              : `Nog ${MAX_DEMO_VRAGEN - gesteld} van ${MAX_DEMO_VRAGEN} vragen in deze demo.`}
          </p>
        </div>
      </form>
    </div>
  );
}
