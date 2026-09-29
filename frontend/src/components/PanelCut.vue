<script setup>
defineProps({ panels: Number, cutHeight: Number, meters: Number, bayDepth: { type: Number, default: 0 } })
</script>
<template>
  <div class="panel-cut">
    <div v-for="n in Math.min(panels||0,8)" :key="n" class="panel" :style="{height: `${(cutHeight||1)*40}px`}"></div>
    <p>{{ panels }} 幅 × {{ cutHeight }} m = {{ meters }} m</p>
    <p v-if="bayDepth">裁高已含飘窗进深 {{ bayDepth }} m</p>
  </div>
</template>
