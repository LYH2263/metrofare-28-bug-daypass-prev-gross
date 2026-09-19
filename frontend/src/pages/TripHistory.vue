<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const parse = (s) => { try { return JSON.parse(s) } catch { return null } }
onMounted(async () => {
  const rows = (await getJSON('/api/history')).items
  items.value = rows.map(r => ({ ...r, input: parse(r.input_json), result: parse(r.result_json) }))
})
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <tr><th>#</th><th>时间</th><th>起 → 终</th><th>途经站数</th><th>分段原价</th><th>应付</th><th>一日通</th></tr>
      <tr v-for="h in items" :key="h.id">
        <td>#{{ h.id }}</td>
        <td>{{ h.created_at }}</td>
        <td>{{ h.input?.start }} → {{ h.input?.end }}</td>
        <td>{{ h.result?.hops ?? '—' }}</td>
        <td>{{ h.result?.fare != null ? '¥' + h.result.fare : '—' }}</td>
        <td>{{ h.result?.payable != null ? '¥' + h.result.payable : (h.result?.fare != null ? '¥' + h.result.fare : '—') }}</td>
        <td>{{ h.result?.day_pass ? (h.result.day_pass.capped ? '触顶' : '未触顶') : '—' }}</td>
      </tr>
    </table>
  </div>
</template>
