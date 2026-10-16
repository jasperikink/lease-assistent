import json

import requests

RDW_URL = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"

def normalize_kenteken(kenteken: str) -> str:
    return kenteken.replace(" ", "").replace("-", "").upper()

def fetch_raw(kenteken: str) -> list[dict]:
    response = requests.get(RDW_URL, params={"kenteken": normalize_kenteken(kenteken)})
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    data = fetch_raw("H-702-BH")
    print(json.dumps(data, indent=4))
