# Lease-assistent

Een voorcheck voor binnenkomende leaseaanvragen. Een adviseur plakt een bericht van een klant, zoals het via WhatsApp binnenkomt:

> "Ik sta sinds juli bij de KvK. Ik wil de Audi met kenteken H-702-BH kopen voor 42.000, 48 maanden, 10% slottermijn. Kan dat?"

Een paar seconden later ziet hij welke auto het is, of de aanvraag binnen het beleid past, wat het per maand kost en een conceptantwoord voor de klant. Past het niet, dan staat er ook bij wat wel kan. In dit geval: met 39 maanden en €8.400 aanbetaling, voor €902,04 per maand.

Het beleid en het handboek in `data/` zijn verzonnen voor deze demo en geschreven met behulp van Claude.

## Waarom ik dit gebouwd heb

Ik wilde iets maken dat een leasemaatschappij echt zou kunnen gebruiken, geen algemene chatbot. Dus ik begon met de vraag waar volgens mij een deel van de tijd van een adviseur naartoe gaat. Wellicht bestaat zoiets al intern.

Een ondernemer stuurt een kenteken, een prijs en een looptijd. Voordat de adviseur iets zinnigs kan terugsturen, zoekt hij de auto op bij de RDW, loopt hij het acceptatiebeleid na, rekent hij het maandbedrag uit en schrijft hij een bericht. Geen van die stappen is moeilijk, maar samen kosten ze tijd. En juist het "dit kan niet, maar zo wel" maakt het verschil voor de klant.

## De belangrijkste keuze

Het taalmodel rekent niet en beslist niet.

Een taalmodel is goed in taal: een rommelig bericht begrijpen, de gegevens eruit halen en een uitkomst helder uitleggen. Het is niet betrouwbaar in rekenen, en het kan een regel vergeten die alleen in een prompt staat. Bij een financiële beslissing vind ik dat niet acceptabel. Daarom staan de regels en de rekensom in gewone Python-code met tests, en roept het model die code aan als tool.

Het fijne daarvan: wil je het beleid aanpassen, dan wijzig je een constante in `rules.py` en draai je de tests. Je herschrijft geen prompt en hoopt niet dat het model het oppikt.

## Hoe het werkt

```
Bericht van de klant
      |
      v
  Agent (Claude via LangChain)
      |   kiest zelf welke tool nodig is
      +--> zoek_voertuig     -> RDW open data
      +--> controleer_lease  -> RDW, acceptatieregels en maandbedrag
      +--> zoek_in_beleid    -> RAG over het handboek
      |
      v
Antwoord, conceptbericht en dossier
```

Het model krijgt bij elke vraag een lijst met drie tools, met per tool een beschrijving. Een kenteken met een prijs gaat naar `controleer_lease`, een vraag over btw naar `zoek_in_beleid`. Het oordeel en het maandbedrag in het dossier komen rechtstreeks uit de toolresultaten, niet uit de tekst van het model.

Als de adviseur daarna de looptijd of aanbetaling aanpast, gaat dat via `/controle` direct naar dezelfde check, zonder model ertussen. Dat is sneller, kost geen tokens en geeft elke keer hetzelfde antwoord.

Schrijft een klant in het Engels, dan staat het conceptbericht ook in het Engels. Het handboek is Nederlands, dus de agent zoekt daarin altijd met een Nederlandse zoekvraag. De uitleg voor de adviseur blijft Nederlands.

Een nieuwe auto die nog geen kenteken heeft, kan ook. Dan valt er niets op te halen bij de RDW, dus de controle rekent met een auto van 0 maanden oud en volgt verder hetzelfde beleid.

## RAG

Niet elk bericht gaat over een auto. Voor vragen over voorwaarden zoekt de assistent in een handboek van zes documenten: acceptatiebeleid, algemene voorwaarden, producten, aanvraagproces, FAQ en werkinstructies voor adviseurs.

Zo heb ik het aangepakt:

- **Knippen op kopjes.** Beleid is al per onderwerp opgedeeld, dus elke sectie is één stuk, met het kopje erbij. Op een vast aantal tekens knippen kan een regel doormidden halen. Dat geeft 51 stukken.
- **Eerst simpel, dan meten.** Ik begon met BM25, zoeken op woorden. Daarna schreef ik 32 vragen zoals een klant ze zou stellen, elk met de sectie waar het antwoord staat. Met BM25 alleen staat de juiste sectie in 56% van de gevallen in de top 3.
- **Kijken waar het misgaat.** De missers zijn bijna allemaal synoniemen: "zzp'er" vindt "starter" niet, "papieren" vindt "documenten" niet. BM25 kent geen betekenis.
- **Dus hybrid.** Embeddings (Voyage) zoeken op betekenis. Reciprocal rank fusion voegt de twee ranglijsten samen. Zonder Voyage-key valt het terug op BM25, zodat het altijd werkt.

Het model krijgt de beste drie stukken en mag alleen daarop antwoorden, met de bron erbij. Staat het er niet in, dan verwijst het naar de afdeling Acceptatie. De adviseur ziet de gevonden stukken onder het antwoord.

Als een vraag misgaat, repareer ik de kennisbank en niet de prompt, en zet ik de vraag in de eval. "Welke auto's kan ik bij jullie leasen?" vond eerst niets bruikbaars, omdat dat antwoord verspreid over het handboek stond. Nu staat het in de FAQ en zit de vraag in de eval.

## Wat waar staat

| Bestand | Wat het doet |
| --- | --- |
| `app/rdw.py` | Voertuig ophalen bij de RDW en omzetten naar een getypeerd model |
| `app/rules.py` | Het acceptatiebeleid als code, met redenen die een adviseur zo kan voorlezen |
| `app/calc.py` | Rente op basis van de leeftijd van de auto, maandbedrag met slottermijn |
| `app/rag.py` | Knippen, BM25, embeddings en reciprocal rank fusion |
| `app/agent.py` | De agent en de drie tools |
| `app/main.py` | FastAPI: `/chat`, `/controle`, `/voorbeelden`, het wachtwoord en de React-app |
| `app/voorbeelden.py` | Voorbeeldberichten voor de inbox, met willekeurige echte auto's uit de RDW |
| `app/limieten.py` | Limiet per IP en het inkorten van lange gesprekken |
| `web/` | React en TypeScript (Vite): inbox, gesprek en dossier |
| `tests/` | 62 tests; de RDW, de embeddings en het taalmodel worden nagebootst |
| `evals/` | Retrieval-eval en een eval die controleert of de agent de juiste gegevens uit een bericht haalt |

## Lokaal draaien

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env    # vul je API-key in
pytest
uvicorn app.main:app --reload
```

Daarna draait hij op http://localhost:8000. De gebouwde React-app staat in `static/`. Aan de voorkant werken:

```bash
cd web
npm install
npm run dev      # http://localhost:5173, praat met FastAPI op :8000
npm run build    # bouwt naar ../static
```

De evals:

```bash
python -m evals.run_retrieval    # vindt hij de juiste sectie?
python -m evals.run_extractie    # haalt de agent de juiste gegevens uit een bericht? (gebruikt de API)
```

## Kosten en misbruik

Een demo met een API-key erachter moet je afschermen. Het wachtwoord wordt op de server gecontroleerd. Per IP kunnen er 15 vragen per uur gesteld worden. Berichten zijn maximaal 1.500 tekens, alleen de laatste 6 berichten van een gesprek gaan mee naar het model, en een antwoord is maximaal 1.024 tokens. In de browser staat een teller van 5 vragen, maar dat is gebruiksgemak, geen beveiliging. Daarnaast staat er een uitgavenlimiet in de Anthropic Console.

Eén zwakke plek ken ik: de limiet per IP staat in het geheugen. Op Vercel kunnen meerdere instanties tegelijk draaien, die elk hun eigen tellers bijhouden. Voor productie zou ik dat naar Redis verplaatsen.

## Wat ik nog zou doen

- Echte, geanonimiseerde klantberichten in de evals, en de evals in CI draaien.
- Een reranker op de top 10 als het handboek groter wordt.
- Openstaande terugroepacties en het oordeel over de kilometerstand uit de RDW meenemen in de check.
- Berichten binnenhalen via het WhatsApp Business Platform, met de adviseur als laatste stap. De assistent stuurt nu bewust niets zelf naar de klant.
