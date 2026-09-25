import { reactive } from 'vue'

const KEY = 'sc-market:favorites'
const stored = JSON.parse(localStorage.getItem(KEY) || '[]')

export const favorites = reactive(new Set(stored))

export function toggleFavorite(id) {
  favorites.has(id) ? favorites.delete(id) : favorites.add(id)
  localStorage.setItem(KEY, JSON.stringify([...favorites]))
}
