<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { state, TYPE_LABEL } from './state'
import { api } from './api'
import { favorites, toggleFavorite } from './favorites'
import { fmt } from './list-utils.js'
import SearchBox from './components/SearchBox.vue'
import PriceModal from './components/PriceModal.vue'

const LIMIT = 50
const FILTERS = [['', 'Tutto'], ['item', 'Oggetti'], ['commodity', 'Commodity'], ['mineral', 'Minerali'], ['component', 'Componenti']]
const SORTS = [['name', 'Nome'], ['buy', 'Prezzo acquisto ↑'], ['sell', 'Prezzo vendita ↓']]
const versions = ref([])
const list = ref({ total: 0, items: [] })
const loading = ref(false)
const error = ref('')
const pages = computed(() => Math.max(1, Math.ceil(list.value.total / LIMIT)))
// Indice del primo non-preferito: serve solo per disegnare il divisore "Tutti gli oggetti"
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
      limit: LIMIT, sort: state.sort, favorites: [...favorites],
    })
    if (n === seq) list.value = r
  } catch { if (n === seq) error.value = "Impossibile caricare l'elenco." }
  finally { if (n === seq) loading.value = false }
}

// Ricarica l'elenco quando cambia versione, filtro, ricerca, pagina o ordinamento
watch(() => [state.version, state.type, state.q, state.page, state.sort], load, { immediate: true })

const setType = t => { state.type = t; state.page = 1 }
const onSearch = q => { state.q = q; state.page = 1 }
const onHeart = id => { toggleFavorite(id); state.page = 1; load() } // l'ordine cambia, si riparte da pagina 1
</script>

<template>
  <header class="top">
    <h1>Listino</h1>
    <SearchBox :version="state.version" :model-value="state.q" @search="onSearch" @pick="e => (state.sel = e.id)" />
    <label class="ver">Versione
      <select v-model="state.version" @change="state.page = 1">
        <option v-for="v in versions" :key="v.id" :value="v.id">{{ v.label }}</option>
      </select>
    </label>
  </header>

  <nav class="filters" aria-label="Categoria e ordinamento">
    <div class="filters-group">
      <button v-for="[t, label] in FILTERS" :key="t" :class="{ on: state.type === t }" @click="setType(t)">{{ label }}</button>
    </div>
    <label class="sort">Ordina
      <select v-model="state.sort" @change="state.page = 1">
        <option v-for="[s, label] in SORTS" :key="s" :value="s">{{ label }}</option>
      </select>
    </label>
  </nav>

  <main :aria-busy="loading">
    <p v-if="error" class="err">{{ error }}</p>
    <p v-else-if="!loading && !list.items.length" class="empty">Nessun risultato. Cambia filtro, ricerca o versione.</p>
    <ul v-else class="list">
      <template v-for="(e, i) in list.items" :key="e.id">
        <li v-if="i === firstOtherIndex && i > 0" class="divider">Tutti gli oggetti</li>
        <li>
          <button class="heart" :class="{ on: favorites.has(e.id) }" :aria-pressed="favorites.has(e.id)"
            title="Preferito" @click="onHeart(e.id)">♥</button>
          <button class="entry" @click="state.sel = e.id">
            <span class="name">{{ e.name }}</span>
            <small>{{ TYPE_LABEL[e.type] }}</small>
            <span class="prices" v-if="e.minBuy != null || e.maxSell != null">
              <span v-if="e.minBuy != null" class="buy">Buy {{ fmt(e.minBuy) }}</span>
              <span v-if="e.maxSell != null" class="sell">Sell {{ fmt(e.maxSell) }}</span>
            </span>
          </button>
        </li>
      </template>
    </ul>
    <div v-if="pages > 1" class="pager">
      <button :disabled="state.page <= 1" @click="state.page--">Precedente</button>
      <span>Pagina {{ state.page }} di {{ pages }}</span>
      <button :disabled="state.page >= pages" @click="state.page++">Successiva</button>
    </div>
  </main>

  <PriceModal v-if="state.sel" :id="state.sel" :version="state.version" @close="state.sel = ''" />
</template>
