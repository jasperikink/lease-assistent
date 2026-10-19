import { FormEvent, useState } from "react";
import { NietIngelogd, inloggen } from "../api";
import { Kenteken } from "./Kenteken";

export function Inloggen({ onIngelogd }: { onIngelogd: () => void }) {
  const [wachtwoord, setWachtwoord] = useState("");
  const [fout, setFout] = useState("");
  const [bezig, setBezig] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBezig(true);
    setFout("");
    try {
      await inloggen(wachtwoord);
      onIngelogd();
    } catch (err) {
      setFout(err instanceof NietIngelogd ? "Dat wachtwoord klopt niet." : "De server is niet bereikbaar. Probeer het zo opnieuw.");
    } finally {
      setBezig(false);
    }
  }

  return (
    <main className="inloggen">
      <Kenteken kenteken="DEMO01" />
      <h1>Lease-assistent</h1>
      <p>Een voorcheck voor binnenkomende leaseaanvragen. Vul het wachtwoord in dat je bij de link kreeg.</p>
      <form onSubmit={onSubmit}>
        <label htmlFor="wachtwoord">Wachtwoord</label>
        <div className="inloggen-rij">
          <input
            id="wachtwoord"
            type="password"
            autoComplete="current-password"
            value={wachtwoord}
            onChange={(e) => setWachtwoord(e.target.value)}
            autoFocus
          />
          <button type="submit" disabled={bezig || !wachtwoord}>
            Open de demo
          </button>
        </div>
        {fout && <p className="inloggen-fout" role="alert">{fout}</p>}
      </form>
    </main>
  );
}
