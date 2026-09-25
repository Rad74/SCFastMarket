from fastapi import FastAPI, HTTPException, Query
from db import connect, init

app = FastAPI(title="SC Market API")
init()


@app.get("/api/versions")
def versions():
    with connect() as c:
        rows = c.execute("SELECT id, label FROM versions ORDER BY imported_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.get("/api/entries")
def entries(version: str, type: str = "", q: str = "", sort: str = "name", favorites: str = "",
            page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)):
    where, args = ["version = ?"], [version]
    if type:
        where.append("type = ?"); args.append(type)
    if q:
        where.append("name LIKE ?"); args.append(f"%{q}%")
    w = " AND ".join(where)
    with connect() as c:
        rows = c.execute(
            f"""SELECT e.id, e.name, e.type,
                       (SELECT MIN(buy) FROM prices WHERE entry_id = e.id AND version = e.version AND buy > 0) AS minBuy,
                       (SELECT MAX(sell) FROM prices WHERE entry_id = e.id AND version = e.version AND sell > 0) AS maxSell
                FROM entries e WHERE {w}""", args).fetchall()
    items = [dict(r) for r in rows]
    key = {
        "buy": lambda e: (e["minBuy"] is None, e["minBuy"] or 0),
        "sell": lambda e: (e["maxSell"] is None, -(e["maxSell"] or 0)),
    }.get(sort, lambda e: (e["name"] or "").lower())
    fav_ids = set(favorites.split(",")) if favorites else set()
    ordered = sorted((e for e in items if e["id"] in fav_ids), key=key) + \
              sorted((e for e in items if e["id"] not in fav_ids), key=key)
    start = (page - 1) * limit
    return {"total": len(ordered), "items": ordered[start:start + limit]}


@app.get("/api/suggest")
def suggest(version: str, q: str = Query(min_length=2)):
    with connect() as c:
        rows = c.execute(
            "SELECT id, name, type FROM entries WHERE version = ? AND name LIKE ? "
            "ORDER BY (name LIKE ?) DESC, name COLLATE NOCASE LIMIT 8",
            (version, f"%{q}%", f"{q}%")).fetchall()  # prima chi inizia con q
    return [dict(r) for r in rows]


@app.get("/api/entries/{entry_id}/prices")
def prices(entry_id: str, version: str):
    with connect() as c:
        e = c.execute("SELECT id, name, type FROM entries WHERE id = ? AND version = ?",
                      (entry_id, version)).fetchone()
        if not e:
            raise HTTPException(404, "Voce non trovata in questa versione")
        rows = c.execute("SELECT location, buy, sell, stock FROM prices WHERE entry_id = ? AND version = ?",
                         (entry_id, version)).fetchall()
    row = lambda r, k: {"location": r["location"], "price": round(r[k]), "stock": r["stock"]}
    buy = sorted((row(r, "buy") for r in rows if r["buy"]), key=lambda x: x["price"])
    sell = sorted((row(r, "sell") for r in rows if r["sell"]), key=lambda x: -x["price"])
    return {"entry": dict(e), "buy": buy, "sell": sell}
