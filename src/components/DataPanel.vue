<script setup>
import { ref, computed, onMounted } from 'vue'
import { state } from '../state'
import { customItems, importCustomItems, clearCustomItems } from '../custom-items'
import { manualPrices, importManualPrices, clearManualPrices } from '../manual-prices'

const emit = defineEmits(['close'])
const dlg = ref()
const fileInput = ref()
const message = ref('')
const lastExport = ref(localStorage.getItem('sc-market:last-export') || '')

const manualCount = computed(() => Object.values(manualPrices)
  .reduce((n, p) => n + (p.buy?.length || 0) + (p.sell?.length || 0), 0))

onMounted(() => dlg.value.showModal())

function exportData() {
  const payload = {
    exportedAt: new Date().toISOString(),
    version: state.version,
    customItems: JSON.parse(JSON.stringify(customItems)),
    manualPrices: JSON.parse(JSON.stringify(manualPrices)),
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `sc-market-export-${payload.version || 'data'}.json`
  a.click()
  URL.revokeObjectURL(url)
  localStorage.setItem('sc-market:last-export', payload.exportedAt)
  lastExport.value = payload.exportedAt
  message.value = 'Downloaded. Run scripts/merge_local.py on this file, then commit and push.'
}

const triggerImport = () => fileInput.value.click()

async function onFile(ev) {
  const file = ev.target.files[0]
  ev.target.value = '' // permette di ricaricare lo stesso file una seconda volta, se serve
  if (!file) return
  try {
    const payload = JSON.parse(await file.text())
    importCustomItems(payload.customItems)
    importManualPrices(payload.manualPrices)
    message.value = 'Imported into this browser.'
  } catch {
    message.value = 'That file could not be read.'
  }
}

function clearAll() {
  if (!confirm('Remove all custom products and manual prices from this browser? This cannot be undone.')) return
  clearCustomItems()
  clearManualPrices()
  message.value = 'Cleared.'
}
</script>

<template>
  <dialog ref="dlg" @close="emit('close')" @click.self="dlg.close()">
    <header>
      <h2>My local data</h2>
      <button class="close" @click="dlg.close()">Close</button>
    </header>

    <p class="hint">
      {{ customItems.length }} custom product(s), {{ manualCount }} manual price(s) — saved only in this browser.
      <template v-if="lastExport">Last export: {{ new Date(lastExport).toLocaleString() }}.</template>
    </p>

    <div class="data-actions">
      <button class="primary" @click="exportData">Export as file</button>
      <button @click="triggerImport">Import from file</button>
      <input ref="fileInput" type="file" accept="application/json" hidden @change="onFile" />
    </div>
    <p v-if="message" class="hint">{{ message }}</p>

    <p class="hint">
      Export gives you a JSON file. Running <code>scripts/merge_local.py</code> on it merges your additions
      into the site's shared data — commit and push to publish them for everyone.
    </p>

    <button class="delete-product" @click="clearAll">Clear local data</button>
  </dialog>
</template>
