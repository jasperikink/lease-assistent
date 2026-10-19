import { FormEvent, useEffect, useState } from "react";
import { Controle, Herberekening } from "../api";

type Props = { controle: Controle; onHerbereken: (invoer: Herberekening) => Promise<void> };

type Velden = {
  aankoopprijs: string;
  aanbetaling: string;
  looptijd: string;
  slottermijn: string;
  kvk: string;
};

function uitControle(c: Controle): Velden {
  return {
    aankoopprijs: String(c.invoer.aankoopprijs),
    aanbetaling: String(c.invoer.aanbetaling),
    looptijd: String(c.invoer.looptijd_maanden),
    slottermijn: String(Math.round(c.invoer.slottermijn_pct * 100)),
    kvk: c.invoer.kvk_maanden === null ? "" : String(c.invoer.kvk_maanden),
  };
}

const getal = (waarde: string) => Number(waarde.replace(/\./g, "").replace(",", ".")) || 0;

export function Invoer({ controle, onHerbereken }: Props) {
  const [velden, setVelden] = useState(() => uitControle(controle));
  const [bezig, setBezig] = useState(false);
  const [fout, setFout] = useState("");

  useEffect(() => setVelden(uitControle(controle)), [controle]);

  const gewijzigd = JSON.stringify(velden) !== JSON.stringify(uitControle(controle));

  function zet(veld: keyof Velden, waarde: string) {
    setVelden((v) => ({ ...v, [veld]: waarde }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBezig(true);
    setFout("");
    try {
      await onHerbereken({
        kenteken: controle.voertuig.kenteken,
        aankoopprijs: getal(velden.aankoopprijs),
        aanbetaling: getal(velden.aanbetaling),
        looptijd_maanden: Math.round(getal(velden.looptijd)),
        slottermijn_pct: getal(velden.slottermijn) / 100,
        kvk_maanden: velden.kvk.trim() === "" ? null : Math.round(getal(velden.kvk)),
      });
    } catch (err) {
      setFout(err instanceof Error ? err.message : "Herberekenen mislukt.");
    } finally {
      setBezig(false);
    }
  }

  const veld = (id: keyof Velden, label: string, eenheid: string) => (
    <div className="veld">
      <label htmlFor={id}>{label}</label>
      <span className="veld-invoer">
        <input id={id} inputMode="decimal" value={velden[id]} onChange={(e) => zet(id, e.target.value)} />
        <span>{eenheid}</span>
      </span>
    </div>
  );

  return (
    <form className="invoer-formulier" onSubmit={onSubmit}>
      <h3 className="invoer-kop">Gerekend met</h3>
      {veld("aankoopprijs", "Aankoopprijs", "€")}
      {veld("aanbetaling", "Aanbetaling", "€")}
      {veld("looptijd", "Looptijd", "mnd")}
      {veld("slottermijn", "Slottermijn", "%")}
      {veld("kvk", "Bij de KvK", "mnd")}
      <div className="veld">
        <span className="veld-label">Rente</span>
        <span className="veld-waarde">{controle.rente_pct.toLocaleString("nl-NL")}%</span>
      </div>
      <button type="submit" disabled={!gewijzigd || bezig}>
        {bezig ? "Rekenen" : "Herbereken"}
      </button>
      <p className="invoer-uitleg">Herberekenen gebruikt alleen de regels en de rekensom, geen AI.</p>
      {fout && <p className="invoer-fout" role="alert">{fout}</p>}
    </form>
  );
}
