<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const s = ref({})
const dp = ref({ day: '', cap: 0, enabled: false })
const msg = ref('')
const err = ref('')
onMounted(async () => {
  s.value = await getJSON('/api/settings')
  dp.value = await getJSON('/api/day-pass')
})
const save = async () => {
  msg.value = ''; err.value = ''
  try {
    dp.value = await putJSON('/api/day-pass', { day: dp.value.day, cap: Number(dp.value.cap), enabled: dp.value.enabled })
    msg.value = '已保存'
  } catch (e) {
    err.value = '保存失败：' + e.message
  }
}
</script>
<template>
  <div class="page"><h1>设置</h1>
    <div class="panel">
      <h2>一日通封顶</h2>
      <p><label>自然日 <input type="date" v-model="dp.day" /></label></p>
      <p><label>封顶金额 <input type="number" min="0.01" step="0.01" v-model="dp.cap" /></label></p>
      <p><label><input type="checkbox" v-model="dp.enabled" /> 启用</label></p>
      <button @click="save">保存</button>
      <span v-if="msg" class="muted"> {{ msg }}</span>
      <span v-if="err"> {{ err }}</span>
    </div>
    <div class="panel"><pre>{{ s }}</pre></div>
  </div>
</template>
