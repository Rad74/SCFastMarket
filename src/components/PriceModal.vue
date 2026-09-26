<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { TYPE_LABEL } from '../state'
import { isCustom, customItems, addCustomPrice, removeCustomPrice, removeCustomItem } from '../custom-items'
import { manualPrices, addManualPrice, removeManualPrice } from '../manual-prices'

const props = defineProps({ id: String, version: String })
const emit = defineEmits(['close'])
const dlg = ref()
const data = ref(null)
const tab = ref('buy')
const error = ref('')
const HINT = { buy: 'Where to buy, from the lowest price', sell: 'Where to sell, from the highest price' }
const fmt = n => new Intl.NumberFormat('en-US').format(n)

// 'custom': prodotto interamente tuo (ogni riga è tua, puoi cancellare il prodotto).
// 'remote': oggetto del DB; le righe reali non si toccano, ma puoi aggiungere le tue.
const mode = computed(() => (isCustom(props.id) ? 'custom' : 'remote'))
const newLocation = ref('')
const newPrice = ref('')

onMounted(() => dlg.value.showModal())

// Marca ogni riga con manual:true/false e mIdx (la sua posizione nell'array "manuale" di origine),
// così sappiamo sempre quale riga rimuovere, a prescindere dall'ordine con cui viene mostrata.
const tagManual = (rows, mIdx0 = 0) => rows.map((r, i) => ({ ...r, manual: true, mIdx: i }))
const tagRemote = rows => rows.map(r => ({ ...r, manual: false }))

async function load() {
  error.value = ''
  if (mode.value === 'custom') {
    const item = customItems.find(e => e.id === props.id)
    data.value = item
      ? { entry: { id: item.id, name: item.name, type: item.type }, buy: tagManual(item.buy), sell: tagManual(item.sell) }
      : null
    return
  }
  data.value = null
  try {
    const remote = await api.prices(props.id, { version: props.version })
    const manual = manualPrices[props.id] || { buy: [], sell: [] }
    const buy = [...tagRemote(remote.buy), ...tagManual(manual.buy)].sort((a, b) => a.price - b.price)
    const sell = [...tagRemote(remote.sell), ...tagManual(manual.sell)].sort((a, b) => b.price - a.price)
    data.value = { entry: remote.entry, buy, sell }
  } catch { error.value = 'Could not load prices. Please try again shortly.' }
}

watch(() => [props.id, props.version], load, { immediate: true })

function addRow() {
  if (!newLocation.value.trim() || newPrice.value === '') return
  const row = { location: newLocation.value.trim(), price: newPrice.value }
  if (mode.value === 'custom') addCustomPrice(props.id, tab.value, row)
  else addManualPrice(props.id, tab.value, row)
  newLocation.value = ''; newPrice.value = ''
  load()
}
function removeRow(row) {
  if (mode.value === 'custom') removeCustomPrice(props.id, tab.value, row.mIdx)
  else removeManualPrice(props.id, tab.value, row.mIdx)
  load()
}
function deleteProduct() {
  removeCustomItem(props.id)
  dlg.value.close() // scatena il close nativo, che chiude e ricarica l'elenco nel genitore
}
</script>

<template>
  <dialog ref="dlg" @close="emit('close')" @click.self="dlg.close()">
    <header>
      <div>
        <h2>{{ data?.entry.name ?? 'Loading…' }}</h2>
        <p v-if="data">
          <span>{{ TYPE_LABEL[data.entry.type] }}</span>
          <span v-if="mode === 'custom'">Custom product · saved in this browser</span>
          <span v-else>{{ version }}</span>
        </p>
      </div>
      <button class="close" @click="dlg.close()">Close</button>
    </header>

    <div class="tabs" role="tablist">
      <button v-for="t in ['buy', 'sell']" :key="t" role="tab" :aria-selected="tab === t"
        :class="[t, { on: tab === t }]" @click="tab = t">{{ t === 'buy' ? 'Buy' : 'Sell' }}</button>
    </div>

    <p v-if="error" class="err">{{ error }}</p>
    <template v-else-if="data">
      <p class="hint">{{ HINT[tab] }}</p>
      <table v-if="data[tab].length">
        <thead><tr><th>Location</th><th class="n">Price (aUEC)</th><th class="n">Stock</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(r, i) in data[tab]" :key="i">
            <td>{{ r.location }}<small v-if="r.manual"> · added by you</small></td>
            <td class="n">{{ fmt(r.price) }}</td>
            <td class="n">{{ r.stock == null ? '–' : fmt(r.stock) }}</td>
            <td class="n"><button v-if="r.manual" class="row-remove" title="Remove" @click="removeRow(r)">×</button></td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">No {{ tab === 'buy' ? 'buy' : 'sell' }} data yet{{ mode === 'remote' ? ' in this version' : '' }}. Add one below.</p>

      <form class="add-row" @submit.prevent="addRow">
        <input v-model="newLocation" type="text" placeholder="Location" required />
        <input v-model="newPrice" type="number" min="0" step="1" placeholder="Price" required />
        <button type="submit">Add {{ tab }} price</button>
      </form>
      <button v-if="mode === 'custom'" class="delete-product" @click="deleteProduct">Delete this product</button>
    </template>
  </dialog>
</template>
