<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { TYPE_LABEL } from '../state'
import { isCustom, customItems, addCustomPrice, removeCustomPrice, removeCustomItem } from '../custom-items'

const props = defineProps({ id: String, version: String })
const emit = defineEmits(['close'])
const dlg = ref()
const data = ref(null)
const tab = ref('buy')
const error = ref('')
const HINT = { buy: 'Where to buy, from the lowest price', sell: 'Where to sell, from the highest price' }
const fmt = n => new Intl.NumberFormat('en-US').format(n)

const editable = computed(() => isCustom(props.id))
const newLocation = ref('')
const newPrice = ref('')

onMounted(() => dlg.value.showModal())

async function load() {
  if (editable.value) {
    // Riferimento diretto agli array reattivi del prodotto: si aggiornano da soli quando li modifichi
    const item = customItems.find(e => e.id === props.id)
    data.value = item ? { entry: { id: item.id, name: item.name, type: item.type }, buy: item.buy, sell: item.sell } : null
    return
  }
  data.value = null; error.value = ''
  try { data.value = await api.prices(props.id, { version: props.version }) }
  catch { error.value = 'Could not load prices. Please try again shortly.' }
}

watch(() => [props.id, props.version], load, { immediate: true })

function addRow() {
  if (!newLocation.value.trim() || newPrice.value === '') return
  addCustomPrice(props.id, tab.value, { location: newLocation.value.trim(), price: newPrice.value })
  newLocation.value = ''; newPrice.value = ''
}
const removeRow = i => removeCustomPrice(props.id, tab.value, i)
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
          <span v-if="editable">Custom product · saved in this browser</span>
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
        <thead><tr><th>Location</th><th class="n">Price (aUEC)</th><th class="n">Stock</th><th v-if="editable"></th></tr></thead>
        <tbody>
          <tr v-for="(r, i) in data[tab]" :key="i">
            <td>{{ r.location }}</td><td class="n">{{ fmt(r.price) }}</td>
            <td class="n">{{ r.stock == null ? '–' : fmt(r.stock) }}</td>
            <td v-if="editable" class="n"><button class="row-remove" title="Remove" @click="removeRow(i)">×</button></td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">No terminal {{ tab === 'buy' ? 'sells' : 'buys' }} this item{{ editable ? '' : ' in this version' }}.</p>

      <form v-if="editable" class="add-row" @submit.prevent="addRow">
        <input v-model="newLocation" type="text" placeholder="Location" required />
        <input v-model="newPrice" type="number" min="0" step="1" placeholder="Price" required />
        <button type="submit">Add {{ tab }} price</button>
      </form>
      <button v-if="editable" class="delete-product" @click="deleteProduct">Delete this product</button>
    </template>
  </dialog>
</template>
