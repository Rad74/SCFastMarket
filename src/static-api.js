// Legge i file JSON generati da scripts/build_data.py, in public/data/.
// Nessun server: filtri, ricerca, ordinamento e paginazione girano nel browser.
// Il dataset è piccolo (migliaia di voci al massimo), quindi va bene.
import { orderWithFavorites, summarize } from './list-utils.js'

const cache = new Map() // version -> { entries: [...], byId: Map, prices: {...} }

async function loadVersion(version) {
  if (cache.has(version)) return cache.get(version)
  const [entries, prices] = await Promise.all([
    fetch(`/data/${version}/entries.json`).then(r => {
      if (!r.ok) throw new Error(`Version not found: ${version}`)
      return r.json()
    }),
    fetch(`/data/${version}/prices.json`).then(r => (r.ok ? r.json() : {})),
  ])
  const data = { entries, byId: new Map(entries.map(e => [e.id, e])), prices }
  cache.set(version, data)
  return data
}

export const staticApi = {
  versions: () => fetch('/data/versions.json').then(r => r.json()),

  async entries({ version, type = '', q = '', page = 1, limit = 50, sort = 'name', favorites = [], custom = [] }) {
    const { entries, prices } = await loadVersion(version)
    const needle = q.trim().toLowerCase()
    const remote = entries
      .filter(e => (!type || e.type === type) && (!needle || e.name.toLowerCase().includes(needle)))
      .map(e => ({ ...e, minBuy: prices[e.id]?.buy[0]?.price ?? null, maxSell: prices[e.id]?.sell[0]?.price ?? null }))
    const own = custom
      .filter(e => (!type || e.type === type) && (!needle || e.name.toLowerCase().includes(needle)))
      .map(summarize)
    const ordered = orderWithFavorites([...own, ...remote], sort, favorites)
    const start = (page - 1) * limit
    return { total: ordered.length, items: ordered.slice(start, start + limit) }
  },

  async suggest({ version, q, custom = [] }) {
    const { entries } = await loadVersion(version)
    const needle = q.trim().toLowerCase()
    if (needle.length < 2) return []
    const remote = entries
      .filter(e => e.name.toLowerCase().includes(needle))
      .sort((a, b) => a.name.toLowerCase().indexOf(needle) - b.name.toLowerCase().indexOf(needle))
    const own = custom.filter(e => e.name.toLowerCase().includes(needle))
    return [...own, ...remote].slice(0, 8)
  },

  async prices(id, { version }) {
    const { byId, prices } = await loadVersion(version)
    const entry = byId.get(id)
    if (!entry) throw new Error('Voce non trovata in questa versione')
    return { entry, buy: prices[id]?.buy ?? [], sell: prices[id]?.sell ?? [] }
  },
}
