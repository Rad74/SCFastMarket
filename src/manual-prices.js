import { reactive } from 'vue'

const KEY = 'sc-market:manual-prices'
const stored = JSON.parse(localStorage.getItem(KEY) || '{}')

// { [entryId]: { buy: [{location,price,stock:null}], sell: [...] } }
export const manualPrices = reactive(stored)

const save = () => localStorage.setItem(KEY, JSON.stringify(manualPrices))

function ensure(id) {
  if (!manualPrices[id]) manualPrices[id] = { buy: [], sell: [] }
  return manualPrices[id]
}

export function addManualPrice(id, kind, { location, price }) {
  ensure(id)[kind].push({ location, price: Number(price), stock: null })
  save()
}

export function removeManualPrice(id, kind, index) {
  const item = manualPrices[id]
  if (!item) return
  item[kind].splice(index, 1)
  save()
}
