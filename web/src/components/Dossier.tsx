import { Controle, Herberekening, Voertuig, euro } from "../api";
import { Invoer } from "./Invoer";
import { Kenteken } from "./Kenteken";

const netjes = (tekst: string) =>
  tekst.toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());

const maand = (iso: string) =>
  new Date(iso).toLocaleDateString("nl-NL", { month: "long", year: "numeric" });

type Props = {
  controle: Controle | null;
  voertuig: Voertuig | null;
  herberekend: boolean;
  onHerbereken: (invoer: Herberekening) => Promise<Controle>;
};

export function Dossier({ controle, voertuig, herberekend, onHerbereken }: Props) {
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
      <Kenteken kenteken={auto.kenteken || "NIEUW"} />
      <h2 className="auto">{auto.kenteken ? netjes(naam) : naam}</h2>
      <p className="auto-meta">
        {auto.kenteken
          ? `${auto.voertuigsoort}, eerste toelating ${maand(auto.eerste_toelating)}`
          : `${auto.voertuigsoort}, nieuw, nog geen kenteken`}
      </p>

      {controle && (
        <>
          <div className="oordeel-rij">
            <div className={`oordeel ${controle.geaccepteerd ? "ja" : "nee"}`}>
              {controle.geaccepteerd ? "Past binnen het beleid" : "Past niet binnen het beleid"}
            </div>
            {herberekend && <span className="herberekend">Aangepast door adviseur</span>}
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

          <Invoer controle={controle} onHerbereken={onHerbereken} />

          {controle.let_op && <p className="let-op">{controle.let_op}</p>}
        </>
      )}
    </aside>
  );
}
