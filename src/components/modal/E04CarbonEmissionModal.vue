<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ChevronDown, Clock, Database, FileCheck, ShieldCheck, X } from 'lucide-vue-next'
import type { E04SourceDetail, KpiDetailConfig } from '@/types/dashboard'

const props = defineProps<{ detail: KpiDetailConfig }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
const materialExpanded = ref(false)
let chart: echarts.ECharts | null = null

const sourceRows = computed(() => props.detail.detailData as E04SourceDetail[])
const materialDetails = computed(() => sourceRows.value.find(row => row.sourceCode === 'material')?.materialDetails ?? props.detail.materialDetails ?? [])
const totalEmission = computed(() => sourceRows.value.reduce((sum, row) => sum + Number(row.emission || 0), 0))
const updateScale = () => { scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080) }
const formatNumber = (value: number, digits = 2) => Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: digits })
const formatActivity = (row: E04SourceDetail) => `${formatNumber(row.activityValue)} ${row.activityUnit}`
const formatFactor = (row: E04SourceDetail) => row.sourceCode === 'material' || row.emissionFactor === null ? '分项核算' : `${formatNumber(row.emissionFactor, 6)} ${row.factorUnit}`
const summaryColor = (label: string) => label === '数据性质' ? '#ffb347' : label === '累计碳排放' ? '#69e36f' : '#e8f3ff'

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const monthly = props.detail.monthlyData ?? []
  chart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 450,
    tooltip: { trigger: 'axis', textStyle: { fontSize: 13 }, formatter: (params: any[]) => [params[0]?.axisValue ?? '', ...params.map(item => `${item.marker}${item.seriesName}：${formatNumber(item.value)} tCO₂e`)].join('<br/>') },
    legend: { top: 0, right: 8, itemWidth: 12, itemHeight: 8, textStyle: { color: '#b8cce3', fontSize: 13 }, data: ['当月排放', '累计排放'] },
    grid: { left: 62, right: 72, top: 38, bottom: 38 },
    xAxis: { type: 'category', data: monthly.map(item => item.period.replace(/^\d{4}-/, '') + '月'), axisLine: { lineStyle: { color: 'rgba(143,169,200,.28)' } }, axisTick: { show: false }, axisLabel: { color: '#b8cce3', fontSize: 13, margin: 12 } },
    yAxis: [
      { type: 'value', name: '当月 tCO₂e', nameTextStyle: { color: '#8fa9c8', fontSize: 12 }, axisLabel: { color: '#8fa9c8', fontSize: 12 }, splitLine: { lineStyle: { color: 'rgba(143,169,200,.09)' } } },
      { type: 'value', name: '累计 tCO₂e', nameTextStyle: { color: '#8fa9c8', fontSize: 12 }, axisLabel: { color: '#8fa9c8', fontSize: 12 }, splitLine: { show: false } },
    ],
    series: [
      { name: '当月排放', type: 'bar', barWidth: 24, data: monthly.map(item => item.monthlyEmission), itemStyle: { color: '#69e36f', borderRadius: [3, 3, 0, 0] } },
      { name: '累计排放', type: 'line', yAxisIndex: 1, symbol: 'circle', symbolSize: 7, lineStyle: { width: 2, color: '#e8f3ff' }, itemStyle: { color: '#e8f3ff' }, data: monthly.map(item => item.cumulativeEmission) },
    ],
  })
}

function handleResize() { updateScale(); chart?.resize() }
function handleKeydown(event: KeyboardEvent) { if (event.key === 'Escape') emit('close') }
function handleOverlayClick(event: MouseEvent) { if (event.target === event.currentTarget) emit('close') }
watch(() => props.detail.monthlyData, () => nextTick(initChart), { deep: true })
onMounted(() => { updateScale(); nextTick(() => { initChart(); modalRef.value?.focus() }); window.addEventListener('resize', handleResize); window.addEventListener('keydown', handleKeydown) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); window.removeEventListener('keydown', handleKeydown); chart?.dispose(); chart = null })
</script>

<template>
  <div class="e04-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div ref="modalRef" class="e04-modal" :class="{ acceptance: isAcceptanceMode }" :style="{ '--e04-scale': scale }" role="dialog" aria-modal="true" aria-labelledby="e04-modal-title" tabindex="-1">
      <header class="e04-header">
        <h2 id="e04-modal-title"><span>E04</span>项目累计碳排放</h2>
        <button type="button" aria-label="关闭" @click="emit('close')"><X :size="22" /></button>
      </header>

      <section class="e04-summary" aria-label="E04摘要">
        <div v-for="item in detail.summary" :key="item.label" class="summary-card">
          <span>{{ item.label }}</span>
          <div><strong :style="{ color: summaryColor(item.label) }">{{ typeof item.value === 'number' ? formatNumber(item.value) : item.value }}</strong><small v-if="item.unit">{{ item.unit }}</small></div>
        </div>
      </section>

      <div class="demo-notice" role="note"><ShieldCheck :size="16" /><span>{{ detail.demoNotice || '当前活动数据及排放因子为系统演示测试数据，尚未作为正式核算依据。' }}</span><b>DEMO-EF-2026-v0.1</b></div>

      <main class="e04-content">
        <div class="e04-main">
          <section class="panel chart-panel"><h3>{{ detail.chartTitle }}</h3><div ref="chartRef" class="e04-chart" /></section>
          <section class="panel source-panel">
            <div class="panel-heading"><h3>{{ detail.detailTitle }}</h3><span>排放量单位：tCO₂e</span></div>
            <div class="source-table-wrap">
              <table class="source-table">
                <colgroup><col style="width:14%"><col style="width:21%"><col style="width:25%"><col style="width:14%"><col style="width:10%"><col style="width:16%"></colgroup>
                <thead><tr><th>排放来源</th><th>活动数据</th><th>排放因子</th><th>排放量</th><th>占比</th><th>核验状态</th></tr></thead>
                <tbody>
                  <template v-for="row in sourceRows" :key="row.sourceCode">
                    <tr>
                      <td><button v-if="row.sourceCode === 'material'" type="button" class="material-toggle" :aria-expanded="materialExpanded" @click="materialExpanded = !materialExpanded"><ChevronDown :size="14" :class="{ expanded: materialExpanded }" />{{ row.source }}</button><span v-else>{{ row.source }}</span></td>
                      <td class="numeric" :title="formatActivity(row)">{{ formatActivity(row) }}</td>
                      <td :title="`${row.factorName}；${row.factorVersion}`">{{ formatFactor(row) }}</td>
                      <td class="numeric">{{ formatNumber(row.emission) }}</td><td class="numeric">{{ row.share.toFixed(1) }}%</td>
                      <td><span class="verification-tag">{{ row.verificationStatus }}</span></td>
                    </tr>
                    <tr v-if="row.sourceCode === 'material' && materialExpanded" class="material-detail-row"><td colspan="6"><div class="material-grid"><div v-for="item in materialDetails" :key="item.material"><strong>{{ item.material }}</strong><span>{{ formatNumber(item.activityValue) }} {{ item.activityUnit }}</span><span>{{ formatNumber(item.emissionFactor, 3) }} {{ item.factorUnit }}</span><b>{{ formatNumber(item.emission) }} tCO₂e</b></div></div></td></tr>
                  </template>
                </tbody>
                <tfoot><tr><td>合计</td><td>—</td><td>—</td><td class="numeric">{{ formatNumber(totalEmission) }}</td><td class="numeric">100.0%</td><td><span class="verification-tag">待业务核验</span></td></tr></tfoot>
              </table>
            </div>
          </section>
        </div>

        <aside class="e04-side">
          <section class="panel composition-panel"><h3>排放来源构成</h3><div class="composition-list"><div v-for="row in sourceRows" :key="row.sourceCode"><div><span>{{ row.source }}</span><strong>{{ formatNumber(row.emission) }} <small>tCO₂e</small></strong></div><div class="share-track"><i :style="{ width: `${row.share}%` }" /></div><small>{{ row.share.toFixed(1) }}%</small></div></div></section>
          <section class="panel boundary-panel"><h3>当前演示核算边界</h3><ul><li v-for="item in detail.accountingBoundary" :key="item">{{ item }}</li></ul><p>仅用于界面和数据链测试，不代表正式工程核算边界。</p></section>
          <section class="panel quality-panel"><h3>数据质量状态</h3><dl><div><dt>数据性质</dt><dd>demo</dd></div><div><dt>因子版本</dt><dd>DEMO-EF-2026-v0.1</dd></div><div><dt>核验状态</dt><dd class="pending">待业务核验</dd></div><div><dt>证据资料</dt><dd>暂未关联</dd></div><div><dt>统计期末</dt><dd>{{ detail.statisticsAsOf || '未提供' }}</dd></div></dl></section>
        </aside>
      </main>

      <footer class="e04-footer"><div class="footer-info" :title="detail.dataSource"><FileCheck :size="14" /><span>数据来源：MySQL演示核算数据链</span></div><div class="footer-info"><Clock :size="14" /><span>更新时间：{{ detail.updateTime }}</span></div><div class="footer-info pending"><Database :size="14" /><span>核验状态：待业务核验</span></div><button type="button" @click="emit('close')">关闭</button></footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.e04-overlay{position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;overflow:hidden;background:rgba(2,11,24,.76);backdrop-filter:blur(4px);animation:e04Fade .2s ease;&.acceptance{animation:none}}
.e04-modal{width:1436px;height:880px;flex:0 0 1436px;box-sizing:border-box;display:flex;flex-direction:column;overflow:hidden;border:1px solid rgba(105,227,111,.35);border-radius:8px;outline:none;background:linear-gradient(180deg,#07182b,#04101f);box-shadow:0 24px 80px rgba(0,0,0,.64);color:#e8f3ff;transform:scale(var(--e04-scale));animation:e04Rise .25s ease;&.acceptance,&.acceptance *{animation:none!important;transition:none!important}}
.e04-header{height:60px;flex:0 0 60px;display:flex;align-items:center;justify-content:space-between;box-sizing:border-box;padding:0 16px;border-bottom:1px solid rgba(105,227,111,.16);h2{margin:0;display:flex;align-items:baseline;gap:12px;font-size:22px;font-weight:600}h2 span{color:#69e36f;font-size:26px;font-weight:700}button{width:36px;height:36px;display:grid;place-items:center;border:0;border-radius:4px;background:transparent;color:#8fa9c8;cursor:pointer}button:hover,button:focus-visible{background:rgba(105,227,111,.08);color:#e8f3ff;outline:1px solid rgba(105,227,111,.28)}}
.e04-summary{flex:0 0 88px;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;box-sizing:border-box;padding:12px 16px 0}.summary-card{min-width:0;display:flex;flex-direction:column;justify-content:center;padding:8px 14px;box-sizing:border-box;border:1px solid rgba(105,227,111,.15);border-radius:5px;background:rgba(105,227,111,.035);>span{color:#b8cce3;font-size:14px;line-height:20px}>div{min-width:0;display:flex;align-items:baseline;gap:5px;white-space:nowrap}strong{min-width:0;font-family:"DIN Alternate","Roboto Condensed",sans-serif;font-size:28px;line-height:34px;font-weight:700}small{color:#8fa9c8;font-size:13px}}
.demo-notice{flex:0 0 38px;display:flex;align-items:center;gap:8px;box-sizing:border-box;margin:10px 16px 0;padding:0 12px;border:1px solid rgba(255,179,71,.26);border-radius:4px;background:rgba(255,179,71,.07);color:#ffd08a;font-size:13px;span{flex:1}b{font-size:12px;font-weight:600}}
.e04-content{min-height:0;flex:1;display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:12px;box-sizing:border-box;padding:12px 16px}.e04-main,.e04-side{min-width:0;min-height:0;display:flex;flex-direction:column;gap:12px}.panel{min-width:0;min-height:0;box-sizing:border-box;border:1px solid rgba(105,227,111,.15);border-radius:6px;background:rgba(4,22,40,.72);h3{margin:0;color:#e8f3ff;font-size:15px;line-height:22px;font-weight:600}}.chart-panel{flex:0 0 246px;padding:10px 12px}.e04-chart{width:100%;height:202px}.source-panel{flex:1;display:flex;flex-direction:column;overflow:hidden}.panel-heading{height:38px;flex:0 0 38px;display:flex;align-items:center;justify-content:space-between;padding:0 12px;box-sizing:border-box;border-bottom:1px solid rgba(143,169,200,.1);span{color:#8fa9c8;font-size:12px}}.source-table-wrap{min-height:0;flex:1;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:rgba(143,169,200,.48) rgba(143,169,200,.08)}
.source-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:14px;th{height:36px;padding:0 8px;border-bottom:1px solid rgba(143,169,200,.15);background:#071b31;color:#b8cce3;font-size:14px;font-weight:600;text-align:left}td{height:38px;padding:0 8px;border-bottom:1px solid rgba(143,169,200,.08);color:#d9e7f5;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}tbody tr:hover:not(.material-detail-row){background:rgba(105,227,111,.035)}tfoot td{color:#e8f3ff;font-weight:600;background:rgba(105,227,111,.035)}.numeric{font-variant-numeric:tabular-nums;text-align:right}}
.material-toggle{display:inline-flex;align-items:center;gap:4px;padding:0;border:0;background:transparent;color:#e8f3ff;font:inherit;cursor:pointer;svg{transition:transform .15s ease}svg.expanded{transform:rotate(180deg)}}.verification-tag{display:inline-flex;min-width:74px;height:24px;align-items:center;justify-content:center;box-sizing:border-box;padding:0 7px;border:1px solid rgba(255,179,71,.34);border-radius:3px;background:rgba(255,179,71,.08);color:#ffbd67;font-size:12px;font-weight:600}.material-detail-row td{height:auto;padding:8px 10px 10px;background:rgba(47,156,255,.035);white-space:normal}.material-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.material-grid>div{display:grid;grid-template-columns:1fr auto;gap:3px 10px;padding:7px 9px;border:1px solid rgba(47,156,255,.15);border-radius:4px;color:#b8cce3;font-size:12px}.material-grid strong{color:#e8f3ff;font-size:13px}.material-grid b{color:#69e36f;text-align:right}
.e04-side .panel{padding:10px 12px}.composition-panel{flex:1.3}.boundary-panel{flex:.8}.quality-panel{flex:1}.composition-list{margin-top:10px;display:flex;flex-direction:column;gap:9px}.composition-list>div{position:relative;padding-right:46px}.composition-list>div>div:first-child{display:flex;align-items:baseline;justify-content:space-between;gap:8px;font-size:13px}.composition-list strong{font-size:18px;font-variant-numeric:tabular-nums}.composition-list strong small{color:#8fa9c8;font-size:11px;font-weight:400}.composition-list>div>small{position:absolute;right:0;bottom:-2px;color:#b8cce3;font-size:12px}.share-track{height:7px;margin-top:5px;overflow:hidden;border-radius:4px;background:rgba(255,255,255,.06)}.share-track i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,rgba(105,227,111,.48),#69e36f)}.boundary-panel ul{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0 8px;padding:0;list-style:none}.boundary-panel li{padding-left:13px;position:relative;color:#d5e5f4;font-size:13px}.boundary-panel li:before{content:'';position:absolute;left:0;top:7px;width:5px;height:5px;border-radius:50%;background:#69e36f}.boundary-panel p{margin:0;color:#ffbd67;font-size:12px;line-height:18px}.quality-panel dl{margin:9px 0 0}.quality-panel dl div{min-height:27px;display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px solid rgba(143,169,200,.07);font-size:13px}.quality-panel dt{color:#8fa9c8}.quality-panel dd{margin:0;color:#d9e7f5;text-align:right}.quality-panel dd.pending{color:#ffbd67;font-weight:600}
.e04-footer{height:52px;flex:0 0 52px;display:flex;align-items:center;gap:18px;box-sizing:border-box;padding:0 16px;border-top:1px solid rgba(105,227,111,.12)}.footer-info{min-width:0;display:flex;align-items:center;gap:6px;color:#8fa9c8;font-size:12px;white-space:nowrap}.footer-info:first-child{max-width:360px;overflow:hidden}.footer-info:first-child span{overflow:hidden;text-overflow:ellipsis}.footer-info.pending{color:#ffbd67}.e04-footer button{width:120px;height:34px;margin-left:auto;border:1px solid rgba(105,227,111,.35);border-radius:4px;background:rgba(105,227,111,.08);color:#e8f3ff;font-size:14px;cursor:pointer}.e04-footer button:hover,.e04-footer button:focus-visible{background:rgba(105,227,111,.15);outline:none}
@keyframes e04Fade{from{opacity:0}to{opacity:1}}@keyframes e04Rise{from{opacity:0;transform:translateY(12px) scale(var(--e04-scale))}to{opacity:1;transform:translateY(0) scale(var(--e04-scale))}}
</style>
