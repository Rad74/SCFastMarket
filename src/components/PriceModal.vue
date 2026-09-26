<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api'
import { TYPE_LABEL } from '../state'

const props = defineProps({ id: String, version: String })
const emit = defineEmits(['close'])
const dlg = ref()
const data = ref(null)
const tab = ref('buy')
const error = ref('')
const HINT = { buy: 'Where to buy, from the lowest price', sell: 'Where to sell, from the highest price' }
const fmt = n => new Intl.NumberFormat('en-US').format(n)

onMounted(() => dlg.value.showModal()) // <dialog> nativo: Esc e focus trap inclusi

watch(() => [props.id, props.version], async () => {
  data.value = null; error.value = ''
  try { data.value = await api.prices(props.id, { version: props.version }) }
  catch { error.value = 'Could not load prices. Please try again shortly.' }
}, { immediate: true })
</script>

<template>
  <dialog ref="dlg" @close="emit('close')" @click.self="dlg.close()">
    <header>
      <div>
        <h2>{{ data?.entry.name ?? 'Loading…' }}</h2>
        <p v-if="data"><span>{{ TYPE_LABEL[data.entry.type] }}</span> <span>{{ version }}</span></p>
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
        <thead><tr><th>Location</th><th class="n">Price (aUEC)</th><th class="n">Stock</th></tr></thead>
        <tbody>
          <tr v-for="r in data[tab]" :key="r.location">
            <td>{{ r.location }}</td><td class="n">{{ fmt(r.price) }}</td><td class="n">{{ r.stock == null ? '–' : fmt(r.stock) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">No terminal {{ tab === 'buy' ? 'sells' : 'buys' }} this item in this version.</p>
    </template>
  </dialog>
</template>
