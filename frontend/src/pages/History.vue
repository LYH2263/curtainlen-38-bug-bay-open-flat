<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([]); const openId = ref(''); const detail = ref(null); const err = ref('')
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function open(id){
  err.value = ''; detail.value = null
  try { detail.value = await getJSON(`/api/runs/${id}`) } catch(e){ err.value = e.message }
}
function bayTag(r){
  return r.result?.bay_enabled ? `飘窗进深 ${r.result.bay_depth ?? 0}m` : '非飘窗'
}
</script>
<template><div class="page"><h1>记录</h1>
<p><input v-model="openId" placeholder="编号"> <button @click="open(openId)">打开</button></p>
<p v-if="err" class="bad">{{ err }}</p>
<div v-if="detail">
  <h2>#{{ detail.id }}</h2>
  <p>详情主字段：{{ detail.result?.meters }}m · 裁高 {{ detail.result?.cut_height }}m · {{ bayTag(detail) }}</p>
  <p>飘窗摘要：{{ detail.bay_summary?.meters }}m · 裁高 {{ detail.bay_summary?.cut_height }}m
    · 进深 {{ detail.bay_summary?.bay_depth }}m</p>
</div>
<ul><li v-for="r in items" :key="r.id">
  <a href="#" @click.prevent="open(r.id)">#{{ r.id }}</a>
  列表：{{ r.result?.meters }}m · 裁高 {{ r.result?.cut_height }}m
  ｜摘要：{{ r.bay_summary?.meters }}m · 裁高 {{ r.bay_summary?.cut_height }}m
  ｜进深 {{ r.bay_summary?.bay_depth ?? 0 }}m（{{ bayTag(r) }}）
</li></ul>
<p class="hint">列表、详情主字段、飘窗摘要三路裁高与米数均等于写入时的落库快照；进深与裁高分列。窗户页/设置页改进深或开关飘窗只影响此后的新单，不会改写已保存编号。</p>
</div></template>
