import { Controle, Voertuig, euro } from "../api";
import { Kenteken } from "./Kenteken";

const netjes = (tekst: string) =>
  tekst.toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());

const maand = (iso: string) =>
  new Date(iso).toLocaleDateString("nl-NL", { month: "long", year: "numeric" });

function kvkTekst(controle: Controle) {
  const { kvk_maanden, kvk_sinds } = controle.invoer;
  if (kvk_maanden === null) return "Onbekend";
  const sinds = kvk_sinds ? `, sinds ${maand(kvk_sinds)}` : "";
  return `${kvk_maanden} maanden${sinds}`;
}

type Props = { controle: Controle | null; voertuig: Voertuig | null };

export function Dossier({ controle, voertuig }: Props) {
  const auto = controle?.voertuig ?? voertuig;

  if (!auto) {
    return (
      <aside className="dossier dossier-leeg">
        <p>Plak een bericht met een kenteken. Hier verschijnt dan de auto, het oordeel en het maandbedrag.</p>
      </aside>
    );
  }

  const naam = auto.model.startsWith(auto.merk) ? auto.model : `${auto.merk} ${auto.model}`;

  return (
    <aside className="dossier">
      <Kenteken kenteken={auto.kenteken} />
      <h2 className="auto">{netjes(naam)}</h2>
      <p className="auto-meta">
        {auto.voertuigsoort}, eerste toelating {maand(auto.eerste_toelating)}
      </p>

      {controle && (
        <>
          <div className={`oordeel ${controle.geaccepteerd ? "ja" : "nee"}`}>
            {controle.geaccepteerd ? "Past binnen het beleid" : "Past niet binnen het beleid"}
          </div>

          {controle.maandbedrag !== null && (
            <div className="bedrag">
              <span className="bedrag-getal">{euro(controle.maandbedrag)}</span>
              <span className="bedrag-label">per maand</span>
            </div>
          )}

          {controle.redenen.length > 0 && (
            <ul className="redenen">
              {controle.redenen.map((reden) => (
                <li key={reden}>{reden}</li>
              ))}
            </ul>
          )}

          <h3 className="invoer-kop">Gerekend met</h3>
          <dl className="feiten">
            <div>
              <dt>Aankoopprijs</dt>
              <dd>{euro(controle.invoer.aankoopprijs)}</dd>
            </div>
            <div>
              <dt>Aanbetaling</dt>
              <dd>{euro(controle.invoer.aanbetaling)}</dd>
            </div>
            <div>
              <dt>Looptijd</dt>
              <dd>{controle.invoer.looptijd_maanden} maanden</dd>
            </div>
            <div>
              <dt>Slottermijn</dt>
              <dd>
                {controle.invoer.slottermijn_pct > 0
                  ? `${Math.round(controle.invoer.slottermijn_pct * 100)}%, ${euro(controle.slottermijn_eind)}`
                  : "Geen"}
              </dd>
            </div>
            <div>
              <dt>Bij de KvK</dt>
              <dd>{kvkTekst(controle)}</dd>
            </div>
            <div>
              <dt>Rente</dt>
              <dd>{controle.rente_pct.toLocaleString("nl-NL")}%</dd>
            </div>
          </dl>

          {controle.let_op && <p className="let-op">{controle.let_op}</p>}
        </>
      )}
    </aside>
  );
}
