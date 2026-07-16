<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: { name: string; value: number; color?: string }[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateOption()
  window.addEventListener('resize', onResize)
}

function updateOption() {
  if (!chart) return
  const palette = ['#2f9cff', '#69e36f', '#a66cff', '#ffb347']
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    legend: {
      orient: 'vertical',
      right: 0,
      top: 'center',
      textStyle: { color: '#8fa9c8', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['32%', '50%'],
        avoidLabelOverlap: false,
        label: { show: false },
        labelLine: { show: false },
        data: props.data.map((item, index) => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: item.color || palette[index % palette.length] },
        })),
      },
    ],
  })
}

function onResize() {
  chart?.resize()
}

onMounted(initChart)
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})

watch(() => props.data, updateOption, { deep: true })
</script>

<template>
  <div ref="chartRef" class="chart-container" />
</template>
