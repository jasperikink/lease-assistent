function metStreepjes(kenteken: string) {
  return kenteken.replace(/([A-Z])(?=\d)|(\d)(?=[A-Z])/g, "$1$2-");
}

export function Kenteken({ kenteken }: { kenteken: string }) {
  return (
    <div className="plaat" aria-label={`Kenteken ${kenteken}`}>
      <span className="plaat-eu" aria-hidden="true">
        <span className="plaat-sterren">★</span>
        NL
      </span>
      <span className="plaat-tekst">{metStreepjes(kenteken)}</span>
    </div>
  );
}
