<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const useDayPass = ref(false)
const dayPass = ref(null)
const out = ref(null)
onMounted(async () => {
  stations.value = (await getJSON('/api/stations')).items
  dayPass.value = await getJSON('/api/day-pass')
})
const run = async () => {
  out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: true, use_day_pass: useDayPass.value })
}
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <label><input type="checkbox" v-model="useDayPass" /> 一日通</label>
      <button @click="run">试算</button>
      <p v-if="useDayPass && dayPass" class="muted">
        一日通 {{ dayPass.day }} · 封顶 ¥{{ dayPass.cap }} · {{ dayPass.enabled ? '已启用' : '未启用' }}
      </p>
    </div>
    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p>途经站数 {{ out.hops }}</p>
        <p v-if="out.day_pass && out.day_pass.capped">
          分段原价 <s>¥{{ out.day_pass.original_fare }}</s> · 封顶 ¥{{ out.day_pass.cap }} · 已触顶
          · 应付 <span class="hero-num">¥{{ out.payable }}</span>
        </p>
        <p v-else>
          应付 <span class="hero-num">¥{{ out.payable }}</span>
          <span v-if="out.day_pass && out.day_pass.applied" class="muted">（分段原价 ¥{{ out.day_pass.original_fare }}，未触顶）</span>
          <span v-else-if="out.day_pass" class="muted">（一日通未生效，按分段原价 ¥{{ out.day_pass.original_fare }} 计）</span>
        </p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
