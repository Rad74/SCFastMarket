"""Genera i file JSON statici del sito, senza bisogno di un backend acceso.

  python build_data.py                  # versione LIVE letta da UEX
  python build_data.py --label PTU-4.8  # etichetta a scelta

Chiave API (opzionale per gli endpoint pubblici): variabile d'ambiente UEX_API_KEY.
Scrive dentro ../public/data/, che Vite pubblica così com'è: dopo `npm run build`
questi file finiscono in dist/data/ e vengono serviti insieme al resto del sito,
senza nessun server Python da tenere acceso.
"""
import argparse, json, os, sys
from pathlib import Path
import httpx

BASE = os.environ.get("UEX_BASE", "https://uexcorp.space/api/2.0")
OUT = Path(__file__).resolve().parent.parent / "public" / "data"

# Come classificare le voci. Lo script stampa i valori trovati: adatta queste liste.
MINERAL_KINDS = {"Metal", "Mineral"}                               # campo `kind` delle commodity
COMPONENT_SECTIONS = {"Systems", "Propulsion", "Vehicle Weapons"}  # campo `section` delle categorie

PLACE_KEYS = ("city_name", "space_station_name", "outpost_name", "moon_name",
              "planet_name", "orbit_name", "star_system_name")


def call(client, endpoint):
    r = client.get(f"{BASE}/{endpoint}")
    r.raise_for_status()
    j = r.json()
    if j.get("status") != "ok":
        sys.exit(f"{endpoint}: risposta inattesa ({j.get('status')})")
    return j["data"]


def where(r):
    name = r.get("terminal_name") or f"Terminale {r.get('id_terminal')}"
    place = next((r[k] for k in PLACE_KEYS if r.get(k)), "")
    return f"{name} ({place})" if place else name


def add_price(prices, entry_id, r):
    row = lambda k: {"location": where(r), "price": round(r[k]), "stock": None}
    if r.get("price_buy"):
        prices.setdefault(entry_id, {"buy": [], "sell": []})["buy"].append(row("price_buy"))
    if r.get("price_sell"):
        prices.setdefault(entry_id, {"buy": [], "sell": []})["sell"].append(row("price_sell"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label")
    args = ap.parse_args()
    headers = {"Authorization": f"Bearer {os.environ['UEX_API_KEY']}"} if os.environ.get("UEX_API_KEY") else {}

    with httpx.Client(headers=headers, timeout=120) as cl:
        dp = call(cl, "data_parameters")
        dp = dp[0] if isinstance(dp, list) else dp
        version = args.label or f"LIVE-{dp['game_version']}"
        commodities = {c["id"]: c for c in call(cl, "commodities")}
        cprices = call(cl, "commodities_prices_all")
        cats = {c["id"]: c for c in call(cl, "categories")}
        iprices = call(cl, "items_prices_all")

    entries, prices = {}, {}
    for cid, c in commodities.items():                       # catalogo completo, anche senza prezzi
        entries[f"c{cid}"] = {"id": f"c{cid}", "name": c["name"],
                               "type": "mineral" if c.get("kind") in MINERAL_KINDS else "commodity"}
    for r in cprices:
        add_price(prices, f"c{r['id_commodity']}", r)
    for r in iprices:
        cat = cats.get(r.get("id_category"), {})
        eid = f"i{r['id_item']}"
        entries[eid] = {"id": eid, "name": r.get("item_name") or eid,
                         "type": "component" if cat.get("section") in COMPONENT_SECTIONS else "item"}
        add_price(prices, eid, r)
    for row in prices.values():                               # dal più economico / dal più alto
        row["buy"].sort(key=lambda x: x["price"])
        row["sell"].sort(key=lambda x: -x["price"])

    vdir = OUT / version
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "entries.json").write_text(json.dumps(list(entries.values()), ensure_ascii=False), encoding="utf-8")
    (vdir / "prices.json").write_text(json.dumps(prices, ensure_ascii=False), encoding="utf-8")

    vlist_path = OUT / "versions.json"
    vlist = json.loads(vlist_path.read_text(encoding="utf-8")) if vlist_path.exists() else []
    vlist = [v for v in vlist if v["id"] != version] + [{"id": version, "label": version}]
    vlist_path.write_text(json.dumps(vlist, ensure_ascii=False), encoding="utf-8")

    print(f"{version}: {len(entries)} voci, {len(prices)} con prezzi -> {vdir}")
    print("kind commodity trovati:   ", sorted({str(c.get('kind')) for c in commodities.values()}))
    print("sezioni categorie trovate:", sorted({str(c.get('section')) for c in cats.values()}))


if __name__ == "__main__":
    main()
