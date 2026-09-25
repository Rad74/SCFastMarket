<script setup>
import { ref, watch } from 'vue'
import { api } from '../api'
import { TYPE_LABEL } from '../state'

const props = defineProps({ version: String, modelValue: String })
const emit = defineEmits(['search', 'pick'])
const text = ref(props.modelValue)
const items = ref([])
const open = ref(false)
const idx = ref(-1)
let timer

watch(text, v => {
  clearTimeout(timer); idx.value = -1
  if (v.trim().length < 2) { items.value = []; open.value = false; return }
  timer = setTimeout(async () => {
    const r = await api.suggest({ version: props.version, q: v.trim() })
    if (v === text.value) { items.value = r; open.value = r.length > 0 }
  }, 200)
})

const pick = e => { open.value = false; emit('pick', e) }
const submit = () => { open.value = false; emit('search', text.value.trim()) }

function onKey(ev) {
  if (ev.key === 'ArrowDown') idx.value = Math.min(idx.value + 1, items.value.length - 1)
  else if (ev.key === 'ArrowUp') idx.value = Math.max(idx.value - 1, -1)
  else if (ev.key === 'Enter') idx.value >= 0 ? pick(items.value[idx.value]) : submit()
  else if (ev.key === 'Escape') open.value = false
  else return
  ev.preventDefault()
}
</script>

<template>
  <div class="search">
    <input v-model="text" type="search" placeholder="Cerca oggetti, minerali, componenti…"
      role="combobox" aria-expanded="open" aria-controls="sugg" autocomplete="off"
      @keydown="onKey" @blur="open = false" @focus="open = items.length > 0" />
    <ul v-if="open" id="sugg" role="listbox">
      <li v-for="(e, i) in items" :key="e.id" role="option" :aria-selected="i === idx"
        :class="{ on: i === idx }" @mousedown.prevent="pick(e)">
        <span>{{ e.name }}</span><small>{{ TYPE_LABEL[e.type] }}</small>
      </li>
    </ul>
  </div>
</template>
