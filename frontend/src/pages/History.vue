<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([]); const openId = ref(''); const detail = ref(null); const err = ref('')
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function open(id){
  err.value = ''; detail.value = null
  try { detail.value = await getJSON(`/api/runs/${id}`) } catch(e){ err.value = e.message }
}
// 裁高与米数以写入时的落库快照为唯一真相：列表、详情主字段与飘窗摘要同源。
function cut(r){ return r.result?.cut_height }
function meters(r){ return r.result?.meters }
</script>
<template><div class="page"><h1>记录</h1>
<p><input v-model="openId" placeholder="编号"> <button @click="open(openId)">打开</button></p>
<p v-if="err" class="bad">{{ err }}</p>
<div v-if="detail">
  <h2>#{{ detail.id }}</h2>
  <p>详情 {{ meters(detail) }}m · 裁高 {{ cut(detail) }}m
    · 摘要裁高 {{ detail.bay_summary?.cut_height }}m · 摘要米数 {{ detail.bay_summary?.meters }}m
    <span v-if="detail.result?.bay_enabled">（飘窗进深+{{ detail.result?.bay_depth }}m，单列不计重）</span>
  </p>
</div>
<ul><li v-for="r in items" :key="r.id">
  <a href="#" @click.prevent="open(r.id)">#{{ r.id }}</a>
  列表 {{ meters(r) }}m · 裁高 {{ cut(r) }}m · 摘要 {{ r.bay_summary?.cut_height }}m / {{ r.bay_summary?.meters }}m
  <span v-if="r.result?.bay_enabled">（飘窗进深+{{ r.result?.bay_depth }}m）</span>
</li></ul>
<p class="hint">裁高与米数取写入时的落库快照：之后改窗户进深、设置默认进深或关掉再开飘窗，旧单的裁高与米数都不变；三路显示一致。窗户页与设置页的进深只作用于新单。</p>
</div></template>
