import { reactive } from 'vue'

const KEY = 'sc-market:custom-items'
const stored = JSON.parse(localStorage.getItem(KEY) || '[]')

// [{ id, name, type, buy: [{location,price,stock:null}], sell: [...] }]
export const customItems = reactive(stored)

const save = () => localStorage.setItem(KEY, JSON.stringify(customItems))

export const isCustom = id => typeof id === 'string' && id.startsWith('custom-')

export function addCustomItem({ name, type }) {
  const id = 'custom-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7)
  customItems.push({ id, name, type, buy: [], sell: [] })
  save()
  return id
}

export function removeCustomItem(id) {
  const i = customItems.findIndex(e => e.id === id)
  if (i !== -1) { customItems.splice(i, 1); save() }
}

export function addCustomPrice(id, kind, { location, price }) {
  const item = customItems.find(e => e.id === id)
  if (!item) return
  item[kind].push({ location, price: Number(price), stock: null })
  save()
}

export function removeCustomPrice(id, kind, index) {
  const item = customItems.find(e => e.id === id)
  if (!item) return
  item[kind].splice(index, 1)
  save()
}
