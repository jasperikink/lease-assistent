import { useState } from "react";
import Markdown from "react-markdown";

const TOOL_LABELS: Record<string, string> = {
  zoek_voertuig: "RDW opgezocht",
  controleer_lease: "Beleid en maandbedrag gecontroleerd",
  zoek_in_beleid: "Beleid doorzocht",
};

function splits(tekst: string) {
  const match = tekst.match(/\**Bericht aan de klant:?\**:?/i);
  if (!match || match.index === undefined) return { analyse: tekst, klant: null };
  const klant = tekst.slice(match.index + match[0].length).trim().replace(/^["“]|["”]$/g, "");
  return { analyse: tekst.slice(0, match.index).trim(), klant };
}

export function Antwoord({ tekst, tools }: { tekst: string; tools: string[] }) {
  const { analyse, klant } = splits(tekst);
  const [gekopieerd, setGekopieerd] = useState(false);
  const unieke = [...new Set(tools)];

  async function kopieer() {
    if (!klant) return;
    await navigator.clipboard.writeText(klant);
    setGekopieerd(true);
    setTimeout(() => setGekopieerd(false), 2000);
  }

  return (
    <div className="antwoord">
      <div className="analyse">
        <Markdown>{analyse}</Markdown>
      </div>

      {klant && (
        <div className="klantbericht">
          <div className="klantbericht-kop">
            <span>Bericht aan de klant</span>
            <button type="button" onClick={kopieer}>
              {gekopieerd ? "Gekopieerd" : "Kopieer"}
            </button>
          </div>
          <p>{klant}</p>
        </div>
      )}

      {unieke.length > 0 && (
        <p className="bronnen">{unieke.map((t) => TOOL_LABELS[t] ?? t).join(", ")}</p>
      )}
    </div>
  );
}
