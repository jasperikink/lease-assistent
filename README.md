# Lease-assistent

Een assistent voor leaseadviseurs. De adviseur plakt een bericht van een klant, bijvoorbeeld uit WhatsApp:

> "Ik sta sinds juli bij de KvK. Ik wil de Audi met kenteken H-702-BH kopen voor 42.000, 48 maanden, 10% slottermijn. Kan dat?"

Binnen een paar seconden krijgt de adviseur:

- welke auto het is, opgehaald bij de RDW
- of de aanvraag binnen het acceptatiebeleid valt, en zo niet, waarom niet en wat wel kan
- de rente en het maandbedrag
- antwoorden op vragen over beleid en voorwaarden, met de gevonden passages uit het handboek erbij
- een conceptbericht om naar de klant te sturen

De adviseur kan daarna in het dossier looptijd, aanbetaling of slottermijn aanpassen en direct herberekenen. Dat gebeurt zonder AI: alleen de regels en de rekensom.

De demo-inbox haalt bij elke keer openen willekeurige echte auto's uit de RDW op, zodat je steeds andere gevallen ziet.

> Het beleid in `data/` is verzonnen voor dit project en geschreven met behulp van Claude.

## Het belangrijkste ontwerpprincipe

**Het LLM rekent niet en beslist niet.** Regels en berekeningen staan in gewone, geteste Python-code. Het LLM haalt de gegevens uit het bericht, kiest welke tool het aanroept en legt de uitkomst uit. Zo krijg je nooit een verzonnen maandbedrag of een regel die het model "vergeet". Bij een financiële beslissing is dat de enige verantwoorde opzet.

## Hoe het werkt

```
Bericht van klant
      |
      v
  Agent (Claude via LangChain)
      |   kiest zelf welke tools nodig zijn
      +--> zoek_voertuig     -> RDW open data
      +--> controleer_lease  -> RDW + acceptatieregels + maandbedrag
      +--> zoek_in_beleid    -> RAG over het beleid en de FAQ
      |
      v
Antwoord + conceptbericht + welke tools gebruikt zijn
```

| Bestand | Wat het doet |
| --- | --- |
| `app/rdw.py` | Haalt een voertuig op bij de RDW en zet de data om naar een getypeerd model |
| `app/rules.py` | Het acceptatiebeleid als code, met redenen die een adviseur zo kan voorlezen |
| `app/calc.py` | Rente op basis van de leeftijd van de auto, en het maandbedrag met slottermijn |
| `app/rag.py` | RAG-pipeline: knipt het beleid op kopjes, zoekt hybrid (BM25 plus Voyage-embeddings, samengevoegd met reciprocal rank fusion) |
| `app/agent.py` | De LangChain-agent met drie tools |
| `app/main.py` | FastAPI: `/chat` (agent), `/controle` (herberekenen zonder AI), `/voorbeelden`, wachtwoord, en de gebouwde React-app |
| `app/voorbeelden.py` | Demo-berichten met willekeurige echte auto's uit de RDW |
| `app/limieten.py` | Limiet per IP en het inkorten van lange gesprekken |
| `web/` | React + TypeScript (Vite): gesprek, dossier met kentekenplaat en oordeel, kopieerbaar klantbericht |
| `tests/` | Tests voor elke laag; de RDW, de embeddings en het LLM worden gemockt |
| `evals/` | Retrieval-eval (hit@1, hit@3, MRR) en extractie-eval op echte klantberichten |

## Starten

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest
uvicorn app.main:app --reload
```

Open http://localhost:8000. De gebouwde React-app staat in `static/`.

Aan de voorkant werken:

```bash
cd web
npm install
npm run dev      # http://localhost:5173, /chat gaat naar FastAPI op :8000
npm run build    # bouwt naar ../static
```

## Evals

```bash
python -m evals.run_retrieval    # vindt de retrieval de juiste beleidssectie?
python -m evals.run_extractie    # haalt de agent de juiste gegevens uit een klantbericht? (gebruikt de API)
```

De kennisbank in `data/` is een fictief handboek van Voorbeeld Lease B.V., geschreven met behulp van Claude: acceptatiebeleid, algemene voorwaarden, producten, aanvraagproces, FAQ en werkinstructies voor adviseurs, samen 49 secties.

Met alleen BM25 staat bij 30 vragen in 53% van de gevallen de juiste sectie in de top 3. De missers zijn vragen in andere woorden dan het handboek: "zzp'er" in plaats van "starter", "jaarrekening" in plaats van "jaarcijfers", "papieren" in plaats van "documenten". Met `VOYAGE_API_KEY` draait dezelfde eval ook hybrid, zodat je het verschil ziet.

## Online zetten (Vercel)

1. Zet de repo op GitHub en importeer hem in Vercel. Vercel herkent FastAPI in `app/main.py`.
2. Zet bij Settings > Environment Variables: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_WORKSPACE_ID` (als je key niet aan een workspace hangt), `VOYAGE_API_KEY` en `DEMO_WACHTWOORD`.
3. Deploy. De React-app in `static/` wordt via de CDN geserveerd, `/chat` draait als functie.

Zonder `DEMO_WACHTWOORD` is de API open voor iedereen met de link.

## Kosten en misbruik beperken

- Wachtwoord op alle endpoints (`DEMO_WACHTWOORD`).
- Per IP maximaal 15 vragen per uur aan de agent, berichten van maximaal 1.500 tekens, en alleen de laatste 6 berichten van het gesprek gaan mee naar het model.
- Maximaal 1.024 tokens per antwoord en maximaal 10 stappen per agent-run.
- In de browser een teller van 5 demovragen. Dat is gebruiksgemak, geen beveiliging: wie zijn browseropslag leegt, begint opnieuw. De limieten op de server zijn de echte grens.
- Herberekenen in het dossier gebruikt geen AI en telt dus niet mee.

Zet daarnaast een uitgavenlimiet in de Anthropic Console. Op Vercel draaien soms meerdere instanties tegelijk, en elke instantie houdt zijn eigen tellers bij.

## Keuzes en afwegingen

- **Alle redenen tegelijk.** Een afwijzing noemt alles wat misgaat, met de grens en een alternatief ("kies een looptijd van maximaal 39 maanden"). Een adviseur wil de klant in één keer helpen.
- **RDW-fouten zijn geen "niet gevonden".** Ligt de RDW plat, dan meldt de assistent dat eerlijk, in plaats van te zeggen dat het kenteken niet bestaat.
- **Hybrid retrieval in plaats van alleen embeddings.** BM25 is sterk op exacte termen uit het beleid ("slottermijn", "KvK"), embeddings op vragen in andere woorden ("zzp'er", "tussentijds afkopen"). Reciprocal rank fusion combineert de twee ranglijsten zonder dat je scores hoeft te normaliseren. Zonder Voyage-key valt het systeem terug op BM25, zodat het altijd werkt.
- **De adviseur blijft ertussen.** De assistent schrijft een conceptbericht, geen automatisch antwoord aan de klant.

## Volgende stappen

- De extractie-eval uitbreiden met echte (geanonimiseerde) WhatsApp-berichten en in CI draaien.
- Een reranker op de top 10 als het beleid groter wordt.
- Extra RDW-data: openstaande terugroepacties en het oordeel over de kilometerstand meenemen in de check.
