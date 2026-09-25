"""Scarica i prezzi da UEX Corp e li salva come snapshot di una versione di gioco.

  python import_uex.py                  # versione LIVE letta da UEX (es. LIVE-4.7.2)
  python import_uex.py --label PTU-4.8  # etichetta a scelta

Chiave API (opzionale per gli endpoint pubblici): variabile d'ambiente UEX_API_KEY.
"""
import argparse, os, sys
from datetime import datetime, timezone
import httpx
from db import connect, init

BASE = os.environ.get("UEX_BASE", "https://uexcorp.space/api/2.0")

# Come classificare le voci. Lo script stampa i valori trovati: adatta queste liste.
MINERAL_KINDS = {"Metal", "Mineral"}                            # campo `kind` delle commodity
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label")
    args = ap.parse_args()
    headers = {"Authorization": f"Bearer {os.environ['UEX_API_KEY']}"} if os.environ.get("UEX_API_KEY") else {}
    init()

    with httpx.Client(headers=headers, timeout=120) as cl:
        dp = call(cl, "data_parameters")
        dp = dp[0] if isinstance(dp, list) else dp
        version = args.label or f"LIVE-{dp['game_version']}"
        commodities = {c["id"]: c for c in call(cl, "commodities")}
        cprices = call(cl, "commodities_prices_all")
        cats = {c["id"]: c for c in call(cl, "categories")}
        iprices = call(cl, "items_prices_all")

    entries, prices = {}, []
    for cid, c in commodities.items():  # catalogo completo, anche senza prezzi
        entries[f"c{cid}"] = (c["name"], "mineral" if c.get("kind") in MINERAL_KINDS else "commodity")
    for r in cprices:
        if r.get("price_buy") or r.get("price_sell"):
            prices.append((f"c{r['id_commodity']}", version, where(r), r.get("price_buy") or 0, r.get("price_sell") or 0, None))
    for r in iprices:
        cat = cats.get(r.get("id_category"), {})
        eid = f"i{r['id_item']}"
        entries[eid] = (r.get("item_name") or eid, "component" if cat.get("section") in COMPONENT_SECTIONS else "item")
        if r.get("price_buy") or r.get("price_sell"):
            prices.append((eid, version, where(r), r.get("price_buy") or 0, r.get("price_sell") or 0, None))

    with connect() as c:  # snapshot atomico: sostituisce quello con la stessa versione
        c.execute("DELETE FROM entries WHERE version = ?", (version,))
        c.execute("DELETE FROM prices WHERE version = ?", (version,))
        c.executemany("INSERT INTO entries VALUES (?,?,?,?)", [(i, version, n, t) for i, (n, t) in entries.items()])
        c.executemany("INSERT INTO prices VALUES (?,?,?,?,?,?)", prices)
        c.execute("INSERT OR REPLACE INTO versions VALUES (?,?,?)", (version, version, datetime.now(timezone.utc).isoformat()))

    print(f"{version}: {len(entries)} voci, {len(prices)} prezzi")
    print("kind commodity trovati:   ", sorted({str(c.get('kind')) for c in commodities.values()}))
    print("sezioni categorie trovate:", sorted({str(c.get('section')) for c in cats.values()}))


if __name__ == "__main__":
    main()
