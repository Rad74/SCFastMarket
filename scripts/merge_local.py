"""Fonde un export del sito (pannello "My local data" -> Export as file) nei dati statici.

  python merge_local.py sc-market-export-LIVE-4.10.0.json
  python merge_local.py export.json --version LIVE-4.10.0-12519617   # forza la versione

I prodotti personalizzati diventano voci normali del catalogo (entries.json); i prezzi
manuali vengono aggiunti alle righe buy/sell già esistenti per lo stesso id (prices.json).
Rivedi sempre l'export prima di fonderlo: da qui in poi le tue aggiunte diventano visibili
a chiunque visiti il sito, non solo a te.

Dopo aver fatto commit e push, ricordati di premere "Clear local data" nel pannello del
sito (sul browser da cui hai esportato): righe identiche (stessa località e stesso prezzo)
non vengono comunque mostrate due volte, ma è comunque più pulito ripartire da zero.
"""
import argparse
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "data"


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def add_unique(rows, new_rows):
    seen = {(r["location"], r["price"]) for r in rows}
    for r in new_rows:
        key = (r["location"], r["price"])
        if key not in seen:
            rows.append(r)
            seen.add(key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_file")
    ap.add_argument("--version", help="Sovrascrive la versione registrata nel file esportato")
    args = ap.parse_args()

    payload = json.loads(Path(args.export_file).read_text(encoding="utf-8"))
    version = args.version or payload.get("version")
    if not version:
        raise SystemExit("Nessuna versione nel file esportato: specifica --version")

    vdir = OUT / version
    entries_path, prices_path = vdir / "entries.json", vdir / "prices.json"
    entries = load(entries_path, [])
    prices = load(prices_path, {})
    known_ids = {e["id"] for e in entries}

    added = 0
    for item in payload.get("customItems", []):
        if item["id"] not in known_ids:
            entries.append({"id": item["id"], "name": item["name"], "type": item["type"]})
            known_ids.add(item["id"])
            added += 1
        row = prices.setdefault(item["id"], {"buy": [], "sell": []})
        add_unique(row["buy"], item.get("buy", []))
        add_unique(row["sell"], item.get("sell", []))

    touched = 0
    for entry_id, rows in payload.get("manualPrices", {}).items():
        row = prices.setdefault(entry_id, {"buy": [], "sell": []})
        add_unique(row["buy"], rows.get("buy", []))
        add_unique(row["sell"], rows.get("sell", []))
        touched += 1

    for row in prices.values():  # stessa convenzione di build_data.py
        row["buy"].sort(key=lambda r: r["price"])
        row["sell"].sort(key=lambda r: -r["price"])

    vdir.mkdir(parents=True, exist_ok=True)
    entries_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    prices_path.write_text(json.dumps(prices, ensure_ascii=False), encoding="utf-8")
    print(f"{version}: {added} nuovi prodotti, {touched} voci con prezzi aggiuntivi -> {vdir}")
    print("Ora: git add public/data && git commit && git push")


if __name__ == "__main__":
    main()
