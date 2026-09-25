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
