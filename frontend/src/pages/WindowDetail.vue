<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const props = defineProps({ id: String })
const w = ref(null)
const bayEnabled = ref(false)
const bayDepth = ref(null)
const msg = ref('')
const err = ref('')
async function load() {
  w.value = await getJSON(`/api/windows/${props.id}`)
  bayEnabled.value = !!w.value.bay_enabled
  bayDepth.value = w.value.bay_depth
}
onMounted(load)
async function saveBay() {
  msg.value = ''; err.value = ''
  try {
    const depth = bayDepth.value === '' || bayDepth.value === null ? null : Number(bayDepth.value)
    await putJSON(`/api/windows/${props.id}/bay`, { bay_enabled: bayEnabled.value, bay_depth: depth })
    await load()
    msg.value = '已保存'
  } catch (e) { err.value = e.message }
}
</script>
<template><div class="page" v-if="w"><h1>{{ w.name }}</h1><p v-if="w.data_quality==='dirty'" class="bad">{{ w.note }}</p>
<p>宽 {{ w.width }} 高 {{ w.height }} 褶倍 {{ w.fullness }}</p>
<h2>飘窗</h2>
<label><input type="checkbox" v-model="bayEnabled" /> 开启飘窗</label>
<label>进深(m) <input type="number" step="0.01" min="0" v-model="bayDepth" placeholder="留空用默认进深" /></label>
<button @click="saveBay">保存飘窗</button>
<span v-if="msg">{{ msg }}</span><span v-if="err" class="bad">{{ err }}</span>
<p v-if="bayEnabled && (bayDepth === null || bayDepth === '')">未登记进深，测算时按默认进深计算。</p>
</div></template>
