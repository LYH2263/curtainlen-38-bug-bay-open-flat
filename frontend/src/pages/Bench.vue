<script setup>
import { onMounted, ref, watch } from 'vue'
import { getJSON, postJSON, putJSON } from '../api'
import PanelCut from '../components/PanelCut.vue'
const windows = ref([]); const fabrics = ref([]); const wid = ref(1); const fid = ref(1); const out = ref(null)
const bayEnabled = ref(false); const bayDepth = ref(null)
const err = ref(''); const bayMsg = ref('')
onMounted(async () => {
  windows.value = (await getJSON('/api/windows')).items.filter(x=>x.data_quality==='clean')
  fabrics.value = (await getJSON('/api/fabrics')).items.filter(x=>x.data_quality==='clean')
  if (windows.value.length) wid.value = windows.value[0].id
  if (fabrics.value.length) fid.value = fabrics.value[0].id
  syncBay()
})
function syncBay(){
  const w = windows.value.find(x=>x.id===wid.value)
  bayEnabled.value = !!(w && w.bay_enabled)
  bayDepth.value = w ? w.bay_depth : null
}
watch(wid, syncBay)
async function saveBay(){
  bayMsg.value = ''; err.value = ''
  try {
    const depth = bayDepth.value === '' || bayDepth.value === null ? null : Number(bayDepth.value)
    const updated = await putJSON(`/api/windows/${wid.value}/bay`, { bay_enabled: bayEnabled.value, bay_depth: depth })
    const i = windows.value.findIndex(x=>x.id===updated.id)
    if (i >= 0) windows.value[i] = updated
    bayMsg.value = '飘窗已保存'
  } catch (e) { err.value = e.message }
}
async function go(save){
  err.value = ''
  try {
    out.value = save ? await postJSON('/api/estimate',{window_id:wid.value,fabric_id:fid.value,save:true}) : await getJSON(`/api/estimate?window_id=${wid.value}&fabric_id=${fid.value}`)
  } catch (e) { out.value = null; err.value = e.message }
}
</script>
<template><div class="page"><h1>算料</h1>
<select v-model.number="wid"><option v-for="x in windows" :key="x.id" :value="x.id">{{ x.name }}</option></select>
<select v-model.number="fid"><option v-for="x in fabrics" :key="x.id" :value="x.id">{{ x.name }}</option></select>
<div>
<label><input type="checkbox" v-model="bayEnabled" /> 飘窗</label>
<label>进深(m) <input type="number" step="0.01" min="0" v-model="bayDepth" placeholder="留空用默认进深" /></label>
<button @click="saveBay">保存飘窗</button><span v-if="bayMsg">{{ bayMsg }}</span>
</div>
<button @click="go(false)">试算</button><button @click="go(true)">保存</button>
<p v-if="err" class="bad">{{ err }}</p>
<PanelCut v-if="out" :panels="out.panels" :cut-height="out.cut_height" :meters="out.meters" :bay-depth="out.bay_depth" />
</div></template>
