import { mock } from './mock'
import { staticApi } from './static-api'

// Tre modalità dati, scelte con VITE_DATA_MODE nel file .env (vedi .env.example):
//  - mock   (default): dati finti, per sviluppare il frontend senza nulla acceso
//  - static: file JSON in public/data/, generati da scripts/build_data.py, nessun server
//  - api:    un backend FastAPI proprio, se in futuro ti servirà (vedi backend/)
const mode = import.meta.env.VITE_DATA_MODE || 'mock'

const get = async (path, params = {}) => {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null))
  const r = await fetch(`/api${path}?${qs}`)
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

const backendApi = {
  versions: () => get('/versions'),
  // I prodotti personalizzati vivono solo nel browser: il backend non li conosce, quindi non li inoltriamo.
  entries: ({ custom, ...p }) => get('/entries', { ...p, favorites: (p.favorites || []).join(',') }),
  suggest: ({ custom, ...p }) => get('/suggest', p),
  prices: (id, p) => get(`/entries/${encodeURIComponent(id)}/prices`, p),
}

export const api = { mock, static: staticApi, api: backendApi }[mode]
