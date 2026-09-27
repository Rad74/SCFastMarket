r"""Esplora i file locali di Star Citizen con scdatatools, per costruire un catalogo
(nome + categoria) alternativo/complementare a quello di UEX.

Installazione (una volta sola):
  pip install scdatatools

FASE 1 - ESPLORA (obbligatoria prima): la struttura interna dei record cambia da patch a
patch, e non posso verificarla senza accesso ai tuoi file di gioco. Questo comando cerca i
record che sembrano pertinenti e ne stampa uno per intero, così vediamo insieme i campi
reali (nome, categoria, eventuale prezzo base) prima di scrivere l'estrazione vera e propria.

  python scrape_local.py explore "C:\Program Files\Roberts Space Industries\StarCitizen\LIVE" commodit
  python scrape_local.py explore "C:\...\LIVE" item
  python scrape_local.py explore "C:\...\LIVE" ship_item

FASE 2 - CATALOGO: una volta che sappiamo dove sono i campi giusti, adatteremo insieme la
funzione build_catalog_entry() qui sotto (oggi è un segnaposto) e lanceremo:

  python scrape_local.py catalog "C:\...\LIVE" --version LIVE-4.10.0 --out ../public/data/LIVE-4.10.0/entries.local.json

Il file va poi confrontato a mano con entries.json (quello di UEX): stessi nomi = stesso
oggetto, nomi presenti solo qui = oggetti che UEX non ha ancora, nomi presenti solo in
UEX = probabilmente rinominati o rimossi nella tua versione locale.
"""
import argparse
import json
from pathlib import Path


def load_install(path):
    try:
        from scdatatools.sc import StarCitizen
    except ImportError:
        raise SystemExit("Manca scdatatools: esegui  pip install scdatatools")
    p = Path(path)
    if not (p / "Data.p4k").exists():
        raise SystemExit(f"Non trovo Data.p4k dentro {p} — controlla il percorso (di solito .../StarCitizen/LIVE)")
    print(f"Carico {p} ... (con installazioni grandi puo' richiedere qualche minuto)")
    return StarCitizen(str(p))


def explore(args):
    sc = load_install(args.install_path)
    hits = sc.datacore.search_filename(f"*{args.pattern}*")
    print(f"\n{len(hits)} record trovati per il pattern '*{args.pattern}*'\n")
    for r in hits[: args.limit]:
        print(" -", r.filename)
    if not hits:
        print("Nessun risultato: prova un pattern diverso (es. 'commodit', 'item', 'consumable', 'weapon').")
        return
    print(f"\n--- Contenuto completo del primo record ({hits[0].filename}) ---\n")
    print(sc.datacore.dump_record_json(hits[0]))
    print("\nSe questo record ha nome/categoria/prezzo dentro, dimmi in quali campi: adatto build_catalog_entry().")


def build_catalog_entry(record, sc):
    """Da un record DataForge a {id, name, type} per entries.json. Segnaposto: i nomi dei
    campi qui sotto sono ipotesi ragionevoli, non verificate — vanno corretti in base a
    quanto emerso dal comando 'explore' sulla tua installazione."""
    data = json.loads(sc.datacore.dump_record_json(record))
    return {
        "id": f"local-{record.id}",           # nessun ID condiviso con UEX: prefisso separato apposta
        "name": data.get("name") or data.get("Name") or record.filename,
        "type": "item",                        # TODO: dedurre da data[...] una volta noto il campo giusto
    }


def catalog(args):
    sc = load_install(args.install_path)
    hits = sc.datacore.search_filename(f"*{args.pattern}*")
    entries = [build_catalog_entry(r, sc) for r in hits]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(entries)} voci scritte in {out}")
    print("Occhio: sono ancora dati grezzi, probabilmente da ripulire prima di unirli a entries.json")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("explore", help="Cerca e mostra un record di esempio, per capire i campi reali")
    e.add_argument("install_path", help=r'Es. "C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"')
    e.add_argument("pattern", help="Frammento del nome file da cercare, es. 'commodit', 'item'")
    e.add_argument("--limit", type=int, default=20)
    e.set_defaults(func=explore)

    c = sub.add_parser("catalog", help="Estrae un catalogo grezzo {id, name, type} in JSON")
    c.add_argument("install_path")
    c.add_argument("pattern")
    c.add_argument("--out", required=True)
    c.set_defaults(func=catalog)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
