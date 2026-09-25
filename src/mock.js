// Dati finti per sviluppare il frontend senza backend
import { orderWithFavorites } from './list-utils.js'

const V = [{ id: 'LIVE-4.3', label: 'LIVE 4.3' }, { id: 'PTU-4.4', label: 'PTU 4.4' }]
const E = [
  ['c1', 'Agricium', 'commodity'], ['c2', 'Laranite', 'commodity'], ['c3', 'Medical Supplies', 'commodity'],
  ['m1', 'Quantanium', 'mineral'], ['m2', 'Taranite', 'mineral'], ['m3', 'Bexalite', 'mineral'],
  ['p1', 'Bulwark Shield Generator', 'component'], ['p2', 'Hemera Quantum Drive', 'component'], ['p3', 'Bore Power Plant', 'component'],
  ['i1', 'Medpen', 'item'], ['i2', 'Multi-Tool', 'item'], ['i3', 'P4-AR Rifle', 'item'],
].map(([id, name, type]) => ({ id, name, type }))
const LOC = ['Area18 (TDD)', 'Lorville (TDD)', 'Orison (TDD)', 'Port Tressler', 'Everus Harbor', 'Baijini Point']

const wait = v => new Promise(r => setTimeout(() => r(v), 120))
const hash = s => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7)
const match = ({ type = '', q = '' }) => E.filter(e =>
  (!type || e.type === type) && e.name.toLowerCase().includes(q.toLowerCase()))

// Prezzi finti, riusati sia dalla lista (min/max) sia dal dettaglio (tutte le località)
function priceRows(id, version) {
  const base = 20 + (hash(id) % 400)
  const k = version.startsWith('PTU') ? 1.12 : 1 // la "versione" cambia i dati
  const row = (location, f) => ({ location, price: Math.round(base * k * f), stock: hash(id + location) % 900 })
  return {
    buy: LOC.slice(0, 4).map((l, i) => row(l, 1 + i * 0.06)),        // dal più economico
    sell: LOC.slice(2).map((l, i) => row(l, 1.25 - i * 0.05)),       // dal più alto
  }
}

export const mock = {
  versions: () => wait(V),
  async entries({ type, q, page = 1, limit = 50, sort = 'name', favorites = [], version }) {
    const withPrices = match({ type, q }).map(e => {
      const { buy, sell } = priceRows(e.id, version)
      return { ...e, minBuy: buy[0]?.price ?? null, maxSell: sell[0]?.price ?? null }
    })
    const ordered = orderWithFavorites(withPrices, sort, favorites)
    const start = (page - 1) * limit
    return wait({ total: ordered.length, items: ordered.slice(start, start + limit) })
  },
  suggest: p => wait(match({ q: p.q }).slice(0, 8)),
  prices: async (id, { version }) => wait({ entry: E.find(e => e.id === id), ...priceRows(id, version) }),
}
