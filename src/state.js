import { reactive, watch } from 'vue'

export const TYPE_LABEL = { item: 'Item', commodity: 'Commodity', mineral: 'Mineral', component: 'Component' }

// Stato globale, sincronizzato con la query string (?version=&type=&q=&page=&sel=)
const p = new URLSearchParams(location.search)
export const state = reactive({
  version: p.get('version') || '',
  type: p.get('type') || '',
  q: p.get('q') || '',
  page: Number(p.get('page') || 1),
  sel: p.get('sel') || '', // id dell'oggetto aperto nel popup
  sort: p.get('sort') || 'name', // name | buy | sell
})

watch(state, () => {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(state))
    if (v && !(k === 'page' && v === 1) && !(k === 'sort' && v === 'name')) q.set(k, v)
  history.replaceState(null, '', q.toString() ? `?${q}` : location.pathname)
}, { deep: true })
