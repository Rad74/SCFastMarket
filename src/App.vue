<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { state, TYPE_LABEL } from './state'
import { api } from './api'
import { favorites, toggleFavorite } from './favorites'
import { customItems, addCustomItem, isCustom } from './custom-items'
import { fmt } from './list-utils.js'
import SearchBox from './components/SearchBox.vue'
import PriceModal from './components/PriceModal.vue'
import AddProductModal from './components/AddProductModal.vue'

const LIMIT = 50
const FILTERS = [['', 'All'], ['item', 'Items'], ['commodity', 'Commodities'], ['mineral', 'Minerals'], ['component', 'Components']]
const SORTS = [['name', 'Name'], ['buy', 'Buy price ↑'], ['sell', 'Sell price ↓']]
const versions = ref([])
const list = ref({ total: 0, items: [] })
const loading = ref(false)
const error = ref('')
const showAdd = ref(false)
const pages = computed(() => Math.max(1, Math.ceil(list.value.total / LIMIT)))
// Index of the first non-favorite item: only used to draw the "All items" divider
const firstOtherIndex = computed(() => list.value.items.findIndex(e => !favorites.has(e.id)))
let seq = 0

onMounted(async () => {
  versions.value = await api.versions()
  if (!versions.value.some(v => v.id === state.version)) state.version = versions.value[0]?.id ?? ''
})

async function load() {
  if (!state.version) return
  const n = ++seq
  loading.value = true; error.value = ''
  try {
    const r = await api.entries({
      version: state.version, type: state.type, q: state.q, page: state.page,
      limit: LIMIT, sort: state.sort, favorites: [...favorites], custom: [...customItems],
    })
    if (n === seq) list.value = r
  } catch { if (n === seq) error.value = 'Could not load the list.' }
  finally { if (n === seq) loading.value = false }
}

// Reload the list when version, filter, search, page or sort changes
watch(() => [state.version, state.type, state.q, state.page, state.sort], load, { immediate: true })

const setType = t => { state.type = t; state.page = 1 }
const onSearch = q => { state.q = q; state.page = 1 }
const onHeart = id => { toggleFavorite(id); state.page = 1; load() } // order changes, so back to page 1
function onAddProduct({ name, type }) {
  const id = addCustomItem({ name, type })
  showAdd.value = false
  state.sel = id // open the detail popup right away, to add prices
}
</script>

<template>
  <header class="top">
    <h1>SC Fast Market Browser</h1>
    <SearchBox :version="state.version" :model-value="state.q" @search="onSearch" @pick="e => (state.sel = e.id)" />
    <label class="ver">Version
      <select v-model="state.version" @change="state.page = 1">
        <option v-for="v in versions" :key="v.id" :value="v.id">{{ v.label }}</option>
      </select>
    </label>
  </header>

  <nav class="filters" aria-label="Category and sorting">
    <div class="filters-group">
      <button v-for="[t, label] in FILTERS" :key="t" :class="{ on: state.type === t }" @click="setType(t)">{{ label }}</button>
    </div>
    <button class="add-btn" @click="showAdd = true">+ Add product</button>
    <label class="sort">Sort by
      <select v-model="state.sort" @change="state.page = 1">
        <option v-for="[s, label] in SORTS" :key="s" :value="s">{{ label }}</option>
      </select>
    </label>
  </nav>

  <main :aria-busy="loading">
    <p v-if="error" class="err">{{ error }}</p>
    <p v-else-if="!loading && !list.items.length" class="empty">No results. Try a different filter, search or version.</p>
    <ul v-else class="list">
      <template v-for="(e, i) in list.items" :key="e.id">
        <li v-if="i === firstOtherIndex && i > 0" class="divider">All items</li>
        <li>
          <button class="heart" :class="{ on: favorites.has(e.id) }" :aria-pressed="favorites.has(e.id)"
            title="Favorite" @click="onHeart(e.id)">♥</button>
          <button class="entry" @click="state.sel = e.id">
            <span class="name">{{ e.name }}</span>
            <small>{{ TYPE_LABEL[e.type] }}</small>
            <span v-if="isCustom(e.id)" class="badge-custom">Custom</span>
            <span class="prices" v-if="e.minBuy != null || e.maxSell != null">
              <span v-if="e.minBuy != null" class="buy">Buy {{ fmt(e.minBuy) }}</span>
              <span v-if="e.maxSell != null" class="sell">Sell {{ fmt(e.maxSell) }}</span>
            </span>
          </button>
        </li>
      </template>
    </ul>
    <div v-if="pages > 1" class="pager">
      <button :disabled="state.page <= 1" @click="state.page--">Previous</button>
      <span>Page {{ state.page }} of {{ pages }}</span>
      <button :disabled="state.page >= pages" @click="state.page++">Next</button>
    </div>
  </main>

  <PriceModal v-if="state.sel" :id="state.sel" :version="state.version" @close="() => { state.sel = ''; load() }" />
  <AddProductModal v-if="showAdd" @close="showAdd = false" @submit="onAddProduct" />

  <footer class="site-footer">
    <span class="author">by RadWarrior</span>
    <a class="uex-badge" href="https://uexcorp.space" target="_blank" rel="noopener">
      <img src="/uex-logo.png" alt="UEX" @error="$event.target.style.display = 'none'" />
      <span>Powered by UEX</span>
    </a>
  </footer>
</template>
