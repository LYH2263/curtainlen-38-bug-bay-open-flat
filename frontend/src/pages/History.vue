<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([]); const openId = ref(''); const detail = ref(null); const err = ref('')
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function open(id){
  err.value = ''; detail.value = null
  try { detail.value = await getJSON(`/api/runs/${id}`) } catch(e){ err.value = e.message }
}
function listCut(r){ return r.result?.list_cut_height_pin ?? r.result?.cut_height }
function listMeters(r){ return r.result?.list_meters_pin ?? r.result?.meters }
</script>
<template><div class="page"><h1>记录</h1>
<p><input v-model="openId" placeholder="编号"> <button @click="open(openId)">打开</button></p>
<p v-if="err" class="bad">{{ err }}</p>
<div v-if="detail">
  <h2>#{{ detail.id }}</h2>
  <p>详情 {{ detail.result?.meters }}m · 裁高 {{ detail.result?.cut_height }}m
    · 摘要裁高 {{ detail.bay_summary?.cut_height }}m
    <span v-if="detail.result?.bay_enabled">（飘窗+{{ detail.result?.bay_depth }}m）</span>
  </p>
</div>
<ul><li v-for="r in items" :key="r.id">
  <a href="#" @click.prevent="open(r.id)">#{{ r.id }}</a>
  列表 {{ listMeters(r) }}m · 裁高 {{ listCut(r) }}m · 摘要 {{ r.bay_summary?.cut_height }}m
  <span v-if="r.result?.bay_enabled">（飘窗+{{ r.result?.bay_depth }}m）</span>
</li></ul>
<p class="hint">列表 pin / 详情主字段 / 飘窗摘要可能各算各的。改进深或关掉再开飘窗后再打开旧单。</p>
</div></template>
