import json
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from app import agent, rdw, rules

load_dotenv()

CASES = json.loads((Path(__file__).parent / "extractie.json").read_text())
VELDEN = ["kenteken", "aankoopprijs", "looptijd_maanden", "aanbetaling", "slottermijn_pct", "starter"]


def eerste_controle(bericht: str) -> dict | None:
    result = agent.maak_agent().invoke({"messages": [{"role": "user", "content": bericht}]})
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", None) or []:
            if call["name"] == "controleer_lease":
                return call["args"]
    return None


def is_starter(args: dict) -> bool | None:
    if args.get("kvk_sinds"):
        maanden = rules.leeftijd_in_maanden(date.fromisoformat(args["kvk_sinds"]), date.today())
    elif args.get("kvk_maanden") is not None:
        maanden = args["kvk_maanden"]
    else:
        return None
    return maanden < rules.STARTER_GRENS_MAANDEN


def gevonden(args: dict) -> dict:
    return {
        "kenteken": rdw.normalize_kenteken(args["kenteken"]),
        "aankoopprijs": args["aankoopprijs"],
        "looptijd_maanden": args["looptijd_maanden"],
        "aanbetaling": args.get("aanbetaling", 0),
        "slottermijn_pct": args.get("slottermijn_pct", 0),
        "starter": is_starter(args),
    }


def main():
    goed_per_veld = {veld: 0 for veld in VELDEN}
    cases_met_velden = 0
    helemaal_goed = 0

    for case in CASES:
        args = eerste_controle(case["bericht"])
        verwacht = case["verwacht"]
        print(case["bericht"][:70])

        if verwacht.get("vraagt_door"):
            ok = args is None
            helemaal_goed += ok
            print(f"  {'ok ' if ok else 'FOUT'} vraagt door in plaats van te gokken\n")
            continue

        cases_met_velden += 1
        if args is None:
            print("  FOUT geen controle uitgevoerd\n")
            continue

        resultaat = gevonden(args)
        fouten = [v for v in VELDEN if resultaat[v] != verwacht[v]]
        for veld in VELDEN:
            goed_per_veld[veld] += veld not in fouten
        helemaal_goed += not fouten
        for veld in fouten:
            print(f"  FOUT {veld}: verwacht {verwacht[veld]}, kreeg {resultaat[veld]}")
        if not fouten:
            print("  ok")
        print()

    print("Per veld:")
    for veld, goed in goed_per_veld.items():
        print(f"  {veld:<18}{goed}/{cases_met_velden}")
    print(f"\nHelemaal goed: {helemaal_goed}/{len(CASES)}")


if __name__ == "__main__":
    main()
