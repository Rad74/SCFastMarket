<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close', 'submit'])
const dlg = ref()
const name = ref('')
const type = ref('item')

onMounted(() => dlg.value.showModal())

function submit() {
  if (!name.value.trim()) return
  emit('submit', { name: name.value.trim(), type: type.value })
  dlg.value.close()
}
</script>

<template>
  <dialog ref="dlg" @close="emit('close')" @click.self="dlg.close()">
    <header>
      <h2>Add product</h2>
      <button class="close" @click="dlg.close()">Close</button>
    </header>

    <form class="add-form" @submit.prevent="submit">
      <label>Name
        <input v-model="name" type="text" required autofocus placeholder="e.g. Homemade Widget" />
      </label>
      <label>Category
        <select v-model="type">
          <option value="item">Item</option>
          <option value="commodity">Commodity</option>
          <option value="mineral">Mineral</option>
          <option value="component">Component</option>
        </select>
      </label>
      <button type="submit" class="primary">Add product</button>
    </form>
    <p class="hint">Saved only in this browser. You'll add buy/sell prices and locations next.</p>
  </dialog>
</template>
