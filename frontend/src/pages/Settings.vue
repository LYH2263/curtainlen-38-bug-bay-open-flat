<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const s = ref({})
const bayDepth = ref('')
const msg = ref('')
const err = ref('')
onMounted(async () => { s.value = await getJSON('/api/settings'); bayDepth.value = s.value.default_bay_depth ?? '' })
async function save() {
  msg.value = ''; err.value = ''
  try {
    await putJSON('/api/settings/default_bay_depth', { value: String(bayDepth.value) })
    s.value = await getJSON('/api/settings')
    msg.value = '已保存（不影响已保存的测算记录）'
  } catch (e) { err.value = e.message }
}
</script>
<template><div class="page"><h1>设置</h1><p>默认褶倍 {{ s.default_fullness }}</p>
<label>默认飘窗进深(m) <input type="number" step="0.01" min="0" v-model="bayDepth" /></label>
<button @click="save">保存</button>
<span v-if="msg">{{ msg }}</span><span v-if="err" class="bad">{{ err }}</span>
</div></template>
