import { Voorbeeld } from "../api";

type Props = {
  berichten: Voorbeeld[] | null;
  onKies: (tekst: string) => void;
  onVernieuw: () => void;
};

export function Inbox({ berichten, onKies, onVernieuw }: Props) {
  return (
    <section className="inbox" aria-label="Voorbeeldberichten">
      <div className="inbox-kop">
        <h2>Voorbeeldberichten</h2>
        <button type="button" onClick={onVernieuw} disabled={berichten === null}>
          Andere auto's
        </button>
      </div>

      {berichten === null ? (
        <p className="inbox-laden">Berichten ophalen</p>
      ) : (
        <ul>
          {berichten.map((b) => (
            <li key={b.tijd}>
              <button type="button" onClick={() => onKies(b.tekst)}>
                <span className="inbox-afzender">
                  {b.afzender}
                  <time>{b.tijd}</time>
                </span>
                <span className="inbox-tekst">{b.tekst}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="inbox-hint">Zo komen aanvragen binnen via WhatsApp. Kies een bericht, of plak hieronder je eigen bericht.</p>
    </section>
  );
}
