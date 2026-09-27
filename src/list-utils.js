export const fmt = n => new Intl.NumberFormat('it-IT').format(Math.round(n))

const COMPARATORS = {
  name: (a, b) => a.name.localeCompare(b.name),
  buy: (a, b) => (a.minBuy ?? Infinity) - (b.minBuy ?? Infinity),   // dal più economico; senza prezzo, in fondo
  sell: (a, b) => (b.maxSell ?? -Infinity) - (a.maxSell ?? -Infinity), // dal più alto; senza prezzo, in fondo
}

const sortEntries = (items, sort) => [...items].sort(COMPARATORS[sort] || COMPARATORS.name)

// Preferiti (per id) in cima, ordinati come il resto; ognuno dei due gruppi con lo stesso criterio.
export function orderWithFavorites(items, sort, favoriteIds = []) {
  const favs = new Set(favoriteIds)
  const fav = sortEntries(items.filter(e => favs.has(e.id)), sort)
  const rest = sortEntries(items.filter(e => !favs.has(e.id)), sort)
  return [...fav, ...rest]
}

// Riassume un prodotto (proprio o personalizzato) nei due numeri mostrati in card
export function summarize(item) {
  const buy = item.buy || [], sell = item.sell || []
  return {
    id: item.id, name: item.name, type: item.type,
    minBuy: buy.length ? Math.min(...buy.map(r => r.price)) : null,
    maxSell: sell.length ? Math.max(...sell.map(r => r.price)) : null,
  }
}

// Toglie dalle righe manuali quelle già identiche (stessa località e prezzo) tra quelle reali.
// Serve per quando una tua riga viene in seguito "promossa" nel dataset ufficiale: a quel punto
// coincide con una riga reale, e senza questo filtro la vedresti comparire due volte.
export function withoutDuplicates(remoteRows, manualRows) {
  const seen = new Set(remoteRows.map(r => `${r.location}|${r.price}`))
  return manualRows.filter(r => !seen.has(`${r.location}|${r.price}`))
}
