<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { X, AlertTriangle, ShieldCheck, FileCheck, Clock, MapPin } from 'lucide-vue-next'
import type { KpiDetailConfig, KpiDetailBottomItem, TopicTab } from '@/types/dashboard'
import { carbonTabData, monthlyTabData } from '@/data/dashboard.mock'
import S01SafetyProductionModal from './S01SafetyProductionModal.vue'

const props = defineProps<{
  detail: KpiDetailConfig
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const showSuperviseToast = ref(false)
let superviseTimer: ReturnType<typeof setTimeout> | null = null

const themeColor = computed(() => {
  const map: Record<string, string> = {
    green: '#69e36f',
    blue: '#2f9cff',
    purple: '#a66cff',
  }
  return map[props.detail.theme]
})

// E01 筛选
const e01Filter = ref('all')
const e01Categories = [
  { key: 'all', label: '全部' },
  { key: 'wastewater', label: '废水' },
  { key: 'noise', label: '噪声' },
  { key: 'dust', label: '扬尘' },
  { key: 'surface', label: '地表水' },
]

// E01 月度数据（与总数对齐：7月合计2）
const e01TrendData = {
  months: ['2月', '3月', '4月', '5月', '6月', '7月'],
  all: [1, 3, 1, 2, 3, 2],
  dust: [1, 2, 1, 1, 2, 1],
  noise: [0, 1, 0, 1, 1, 1],
  wastewater: [0, 0, 0, 0, 0, 0],
  surface: [0, 0, 0, 0, 0, 0],
}

// E01 分类颜色映射
const e01CatColors: Record<string, string> = {
  dust: '#69e36f',
  noise: '#2f9cff',
  wastewater: '#a66cff',
  surface: '#00e5ff',
}

// E01 动态可用分类（过滤无数据类别）
const e01AvailableCategories = computed(() => {
  const available: typeof e01Categories = [{ key: 'all', label: '全部' }]
  e01Categories.forEach(cat => {
    if (cat.key === 'all') return
    const data = e01TrendData[cat.key as keyof typeof e01TrendData] as number[]
    if (data.some(v => Number(v) > 0)) {
      available.push(cat)
    }
  })
  return available
})

// E01 类别构成数据（优先使用 API categoryData）
const e01CompositionData = computed(() => {
  const apiCategoryData = props.detail.categoryData as { name: string; value: number }[] | undefined
  if (apiCategoryData && apiCategoryData.length > 0) {
    const catColorMap: Record<string, string> = {
      '扬尘': '#69e36f',
      '噪声': '#2f9cff',
      '废水': '#a66cff',
      '地表水': '#00e5ff',
      'dust': '#69e36f',
      'noise': '#2f9cff',
      'wastewater': '#a66cff',
      'surface': '#00e5ff',
    }
    return apiCategoryData
      .filter(cat => cat.name !== '合计')
      .map(cat => ({
        name: cat.name,
        value: cat.value,
        color: catColorMap[cat.name] || '#8fa9c8',
      }))
      .filter(cat => cat.value > 0)
  }
  const total = e01TrendData.all[e01TrendData.all.length - 1] || 0
  const items: Array<{ name: string; value: number; color: string }> = []
  e01Categories.forEach(cat => {
    if (cat.key === 'all') return
    const data = e01TrendData[cat.key as keyof typeof e01TrendData] as number[]
    const value = data[data.length - 1] || 0
    if (value > 0) {
      items.push({
        name: cat.label,
        value,
        color: e01CatColors[cat.key] || '#8fa9c8',
      })
    }
  })
  return items
})

// E01 是否有有效数据
const e01HasData = computed(() => {
  return e01AvailableCategories.value.length > 1 || e01TrendData.all.some(v => v > 0)
})

// 监听可用分类变化，确保选中类别始终有效
watch(e01AvailableCategories, (newCats) => {
  const validKeys = newCats.map(c => c.key)
  if (!validKeys.includes(e01Filter.value)) {
    e01Filter.value = 'all'
  }
}, { immediate: true })

// E02 状态构成（动态计算，使用 mainStatus 避免逾期被计入主状态）
const e02StatusData = computed(() => {
  const items = props.detail.key === 'E02' ? props.detail.detailData : []
  const getStatus = (i: any) => i.mainStatus || i.status
  const rectifying = items.filter(i => getStatus(i) === '整改中').length
  const pendingReview = items.filter(i => getStatus(i) === '待复查').length
  const pendingClose = items.filter(i => getStatus(i) === '待关闭' || getStatus(i) === '待销项').length
  return [
    { name: '整改中', value: rectifying, color: '#69e36f' },
    { name: '待复查', value: pendingReview, color: '#2f9cff' },
    { name: '待销项', value: pendingClose, color: '#ffb347' },
  ]
})

// E02 问题类型（动态计算，过滤0项）
const e02TypeData = computed(() => {
  if (props.detail.key !== 'E02') return []
  const items = props.detail.detailData
  const typeMap: Record<string, number> = {}
  items.forEach(item => {
    const cat = item.category as string
    typeMap[cat] = (typeMap[cat] || 0) + 1
  })
  return Object.entries(typeMap)
    .map(([name, value]) => ({ name, value }))
    .filter(t => t.value > 0)
})

// E02 时限状态计算
function getE02DeadlineStatus(deadline: string): { type: string; text: string } {
  const deadlineDate = new Date(deadline)
  const now = new Date('2026-07-14')
  const diffDays = Math.ceil((deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return { type: 'overdue', text: `逾期${Math.abs(diffDays)}天` }
  if (diffDays === 0) return { type: 'warning', text: '今日到期' }
  if (diffDays <= 3) return { type: 'warning', text: `临期${diffDays}天` }
  return { type: 'normal', text: '正常' }
}

// E02 动态指标卡数据
const e02OverdueCount = computed(() => {
  if (props.detail.key !== 'E02') return 0
  const now = new Date('2026-07-14')
  return props.detail.detailData.filter(
    item => item.status !== '已关闭' && new Date(item.deadline as string) < now
  ).length
})

const e02OverdueMessage = computed(() => {
  return e02OverdueCount.value > 0
    ? `${e02OverdueCount.value}项已超过整改期限`
    : '当前无逾期未闭环事项'
})

// E02 动态指标卡
const e02SummaryCards = computed(() => {
  if (props.detail.key !== 'E02') return []
  const items = props.detail.detailData
  const getStatus = (i: any) => i.mainStatus || i.status
  const unresolved = items.filter(i => getStatus(i) !== '已关闭').length
  const rectifying = items.filter(i => getStatus(i) === '整改中').length
  const pendingReview = items.filter(i => getStatus(i) === '待复查').length
  const pendingClose = items.filter(i => getStatus(i) === '待关闭' || getStatus(i) === '待销项').length
  const overdue = e02OverdueCount.value
  return [
    { label: '当前未闭环事项', value: unresolved, unit: '项' },
    { label: '整改中', value: rectifying, unit: '项', filterField: 'mainStatus', filterValue: '整改中' },
    { label: '待复查', value: pendingReview, unit: '项', filterField: 'mainStatus', filterValue: '待复查' },
    { label: '待销项', value: pendingClose, unit: '项', filterField: 'mainStatus', filterValue: '待销项' },
    { label: '已逾期', value: overdue, unit: '项', filterField: 'overdue', filterValue: 'overdue' },
  ]
})

// E02 筛选与行选择
const e02TableFilter = ref<{ field: string; value: string } | null>(null)
const e02SelectedRow = ref<number | null>(null)

const e02FilteredDetailData = computed(() => {
  if (props.detail.key !== 'E02') return []
  const items = props.detail.detailData
  if (!e02TableFilter.value) return items
  const { field, value } = e02TableFilter.value
  if (field === 'overdue') {
    const now = new Date('2026-07-14')
    return items.filter(item => new Date(item.deadline as string) < now && item.status !== '已关闭')
  }
  return items.filter(item => item[field as string] === value)
})

function e02ToggleFilter(field: string, value: string) {
  if (e02TableFilter.value?.field === field && e02TableFilter.value?.value === value) {
    e02TableFilter.value = null
  } else {
    e02TableFilter.value = { field, value }
  }
}

function e02HandleRowClick(index: number) {
  e02SelectedRow.value = e02SelectedRow.value === index ? null : index
}

const e02CanSupervise = computed(() => {
  if (props.detail.key !== 'E02') return true
  if (e02SelectedRow.value === null) return false
  const item = e02FilteredDetailData.value[e02SelectedRow.value]
  return item && item.status !== '已关闭'
})

// E04 行选择与督办
const e04SelectedRow = ref<number | null>(null)

function e04HandleRowClick(index: number) {
  e04SelectedRow.value = e04SelectedRow.value === index ? null : index
}

const e04CanSupervise = computed(() => {
  if (props.detail.key !== 'E04') return true
  if (e04SelectedRow.value === null) return false
  const item = props.detail.detailData[e04SelectedRow.value]
  return item && (item as any).attention !== '正常'
})

const s02Filter = ref('all')
const s02Categories = [
  { key: 'all', label: '全部' },
  { key: 'major', label: '重大' },
  { key: 'bigger', label: '较大' },
  { key: 'near', label: '临近作业' },
]

const s02RiskPoints = [
  { id: 1, x: 15, y: 58, level: '较大', label: '1', status: '正常管控' },
  { id: 2, x: 28, y: 48, level: '重大', label: '2', status: '正常管控' },
  { id: 3, x: 42, y: 42, level: '较大', label: '3', status: '临近关键作业' },
  { id: 4, x: 55, y: 38, level: '较大', label: '4', status: '持续管控' },
  { id: 5, x: 68, y: 34, level: '较大', label: '5', status: '正常管控' },
  { id: 6, x: 78, y: 30, level: '较大', label: '6', status: '正常管控' },
]

// S02 类型分布
const s02TypeData = [
  { name: '高边坡', value: 2 },
  { name: '隧道', value: 1 },
  { name: '架梁', value: 1 },
  { name: '爆破', value: 1 },
  { name: '交通导改', value: 1 },
]

// S02 治理关注点
const s02ConcernData = [
  { name: '措施缺失', value: 1 },
  { name: '长期未复核', value: 1 },
]

// G02 到期分桶
const g02BucketData = [
  { name: '已逾期', value: 1, color: '#ff4f5e' },
  { name: '7日内', value: 1, color: '#ffb347' },
  { name: '8-15日', value: 1, color: '#a66cff' },
  { name: '16-30日', value: 2, color: '#a66cff' },
  { name: '30日以上', value: 0, color: '#2f9cff' },
]

// G02 预警摘要
const g02WarningData = [
  { name: '夜间施工许可', value: 1 },
  { name: '临时用地许可', value: 1 },
  { name: '爆破作业许可', value: 1 },
  { name: '特种设备许可', value: 1 },
  { name: '临时用电许可', value: 1 },
]

// E03 问题类型分布
const e03TypeData = [
  { name: '截排水', value: 2, color: '#69e36f' },
  { name: '边坡防护', value: 2, color: '#2f9cff' },
  { name: '沉沙设施', value: 1, color: '#00e5ff' },
  { name: '弃渣场', value: 1, color: '#ffb347' },
  { name: '临时占地', value: 1, color: '#a66cff' },
]

// E03 工点风险点
const e03WorkPoints = [
  { id: 1, x: 15, y: 58, label: '1', count: 2, risk: 'high' },
  { id: 2, x: 28, y: 48, label: '2', count: 2, risk: 'high' },
  { id: 3, x: 42, y: 42, label: '3', count: 1, risk: 'normal' },
  { id: 4, x: 55, y: 38, label: '4', count: 1, risk: 'normal' },
  { id: 5, x: 68, y: 34, label: '5', count: 1, risk: 'normal' },
]

// E03 风险摘要
const e03RiskSummary = [
  { name: '汛期高风险（项）', value: 2 },
  { name: '可能影响行洪（项）', value: 1 },
  { name: '可能造成水土流失（项）', value: 3 },
  { name: '一般风险（项）', value: 1 },
]

// E04 时间范围筛选
const e04TimeRange = ref('6m')
const e04TimeRanges = [
  { key: '6m', label: '近6月' },
  { key: '12m', label: '近12月' },
]

// E04 趋势数据（完整核算月，不包含未完成月份）
const e04TrendData = {
  months6: ['1月', '2月', '3月', '4月', '5月', '6月'],
  months12: ['7月', '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月', '4月', '5月', '6月'],
  data6: [0.156, 0.182, 0.168, 0.142, 0.132, 0.128],
  data12: [0.174, 0.171, 0.169, 0.165, 0.161, 0.159, 0.156, 0.182, 0.168, 0.142, 0.132, 0.128],
  target: 0.150,
}

// E04 标段排名
const e04SectionRanking = [
  { name: 'K36+500~K41+000 桥梁段', value: 0.112, normal: true },
  { name: 'K12+300~K16+800 路基段', value: 0.128, normal: true, highlight: true },
  { name: 'K48+150~K52+800 隧道段', value: 0.145, normal: true },
  { name: 'K24+000~K28+500 路基段', value: 0.186, normal: true },
  { name: 'K61+800~K65+200 互通段', value: 0.198, normal: false },
]

// S01 近12月状态
const s01MonthlyStatus = [
  { month: '2025-08', status: '正常' },
  { month: '2025-09', status: '正常' },
  { month: '2025-10', status: '正常' },
  { month: '2025-11', status: '正常' },
  { month: '2025-12', status: '正常' },
  { month: '2026-01', status: '正常' },
  { month: '2026-02', status: '正常' },
  { month: '2026-03', status: '正常' },
  { month: '2026-04', status: '正常' },
  { month: '2026-05', status: '正常' },
  { month: '2026-06', status: '正常' },
  { month: '2026-07', status: '正常' },
]

// S01 时间轴节点
const s01TimelineNodes = [
  { label: '起算节点', value: '2025-07-10', type: 'start' },
  { label: '30天月度复核', value: '2025-08-10', type: 'review' },
  { label: '60天月度复核', value: '2025-09-09', type: 'review' },
  { label: '特殊施工期', value: '2025-10~2025-12', type: 'special' },
  { label: '90天月度复核', value: '2025-10-09', type: 'review' },
  { label: '当前连续', value: '368天', type: 'current' },
]

// S01 计数规则摘要
const s01Rules = [
  '每日按自然日滚动累计，持续无责任事故则天数+1',
  '发生经认定的责任事故，天数从次日开始重新计算',
  '停工期是否计入连续天数，按项目确认口径执行',
]

// G04 问题构成
const g04ProblemData = [
  { name: '资料缺失', value: 1, color: '#a66cff' },
  { name: '已失效', value: 1, color: '#ff4f5e' },
  { name: '未签章', value: 1, color: '#ffb347' },
  { name: '未归档', value: 0, color: '#2f9cff' },
  { name: '版本不一致', value: 1, color: '#69e36f' },
]

// G04 节点影响
const g04NodeImpact = [
  { name: '开工报审', value: 1 },
  { name: '阶段验收', value: 1 },
  { name: '月报编制', value: 1 },
  { name: '档案移交', value: 1 },
]

// S03 纠纷类型分布
const s03TypeData = [
  { name: '工资支付', value: 2, color: '#2f9cff' },
  { name: '退场结算', value: 1, color: '#ffb347' },
  { name: '考勤争议', value: 1, color: '#a66cff' },
]

// S03 风险等级
const s03RiskData = [
  { name: '高风险', value: 1, color: '#ff4f5e' },
  { name: '中风险', value: 2, color: '#ffb347' },
  { name: '一般关注', value: 1, color: '#2f9cff' },
]

// S04 诉求类型分布
const s04TypeData = [
  { name: '通行影响', value: 1, color: '#2f9cff' },
  { name: '施工扰民', value: 1, color: '#ffb347' },
  { name: '征地协调', value: 1, color: '#a66cff' },
]

// S04 沿线位置点
const s04LocationPoints = [
  { id: 1, x: 28, y: 48, label: 'K24', type: 'passage' },
  { id: 2, x: 55, y: 38, label: 'K48', type: 'noise' },
  { id: 3, x: 68, y: 34, label: 'K61', type: 'land' },
]

// G01 办理状态构成
const g01StatusData = [
  { name: '尚未报审', value: 1, color: '#8fa9c8' },
  { name: '材料补正', value: 1, color: '#ffb347' },
  { name: '审批中', value: 3, color: '#a66cff' },
]

// G01 受影响节点
const g01NodeImpact = [
  { name: '开工报审', value: 1 },
  { name: '专项施工', value: 2 },
  { name: '阶段验收', value: 2 },
]

// G03 整改状态构成
const g03StatusData = [
  { name: '整改中', value: 1, color: '#2f9cff' },
  { name: '逾期整改', value: 2, color: '#ff4f5e' },
  { name: '待复查', value: 2, color: '#ffb347' },
  { name: '复查未通过', value: 1, color: '#a66cff' },
]

// G03 检查来源分布
const g03SourceData = [
  { name: '监理检查', value: 2 },
  { name: '项目检查', value: 2 },
  { name: '审计检查', value: 1 },
  { name: '主管部门检查', value: 1 },
]

// 专题标签页
const activeTab = ref('cumulative')
const isTopicMode = computed(() => props.detail.isTopic === true)

// 碳足迹标签页数据
const topicData = computed(() => props.detail.topicData || {})
const carbonCumulativeData = computed(() => topicData.value.cumulative || carbonTabData.cumulative)
const carbonBenefitData = computed(() => topicData.value.benefit || carbonTabData.benefit)
const carbonSourceData = computed(() => topicData.value.source || carbonTabData.source)
const carbonCostData = computed(() => topicData.value.cost || carbonTabData.cost)
const carbonMeasuresData = computed(() => topicData.value.measures || carbonTabData.measures)

// 月报标签页数据
const monthlyProgressData = computed(() => topicData.value.progress || monthlyTabData.progress)
const monthlyChaptersData = computed(() => topicData.value.chapters || monthlyTabData.chapters)
const monthlyStatusChain = computed(() => topicData.value.statusChain || monthlyTabData.statusChain)
const monthlyGroupFilter = ref('all')

const currentChartType = computed(() => props.detail.key)

const filteredS02RiskPoints = computed(() => {
  const filter = s02Filter.value
  if (filter === 'all') return s02RiskPoints
  if (filter === 'major') return s02RiskPoints.filter(p => p.level === '重大')
  if (filter === 'bigger') return s02RiskPoints.filter(p => p.level === '较大')
  if (filter === 'near') return s02RiskPoints.filter(p => p.status === '临近关键作业')
  return s02RiskPoints
})

const filteredS02DetailData = computed(() => {
  const filter = s02Filter.value
  if (!props.detail.detailData) return []
  if (filter === 'all') return props.detail.detailData
  if (filter === 'major') return props.detail.detailData.filter((d: any) => d.level === '重大')
  if (filter === 'bigger') return props.detail.detailData.filter((d: any) => d.level === '较大')
  if (filter === 'near') return props.detail.detailData.filter((d: any) => d.status === '临近关键作业')
  return props.detail.detailData
})

const filteredMonthlyDetailData = computed(() => {
  if (!props.detail.detailData) return []
  if (props.detail.key !== 'MONTHLY') return props.detail.detailData
  const filter = monthlyGroupFilter.value
  if (filter === 'all') return props.detail.detailData
  return props.detail.detailData.filter((d: any) => d.group === filter)
})

function initChart() {
  if (!chartRef.value) return
  if (chart) {
    chart.dispose()
    chart = null
  }
  chart = echarts.init(chartRef.value)
  // E02 图表柱状条点击筛选
  chart.on('click', (params: { name?: string }) => {
    if (props.detail.key !== 'E02') return
    if (!params.name) return
    const statusName = params.name
    if (['整改中', '待复查', '待关闭', '待销项'].includes(statusName)) {
      e02ToggleFilter('mainStatus', statusName)
    }
  })
  updateChart()
}

function updateChart() {
  if (!chart) return
  const key = props.detail.key

  // 专题模式图表
  if (key === 'CARBON') {
    if (activeTab.value === 'cumulative') {
      chart.setOption({
        grid: { top: 30, right: 20, bottom: 30, left: 50 },
        xAxis: {
          type: 'category',
          data: carbonCumulativeData.value.months,
          axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
          axisLabel: { color: '#8fa9c8', fontSize: 10, rotate: 30 },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          axisLabel: { color: '#8fa9c8', fontSize: 11 },
          splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
        },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
        legend: { bottom: 0, textStyle: { color: '#8fa9c8', fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
        series: [
          {
            type: 'bar',
            name: '月度排放',
            data: carbonCumulativeData.value.monthlyData,
            barWidth: 12,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#69e36f' }, { offset: 1, color: 'rgba(105,227,111,0.2)' }]), borderRadius: [2, 2, 0, 0] },
          },
          {
            type: 'line',
            name: '累计排放',
            data: carbonCumulativeData.value.cumulativeData,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { color: '#2f9cff', width: 2 },
            itemStyle: { color: '#2f9cff', borderColor: '#02111f', borderWidth: 2 },
            yAxisIndex: 0,
          },
        ],
      })
    } else if (activeTab.value === 'benefit') {
      chart.setOption({
        grid: { top: 30, right: 20, bottom: 30, left: 50 },
        xAxis: {
          type: 'category',
          data: carbonBenefitData.value.months,
          axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
          axisLabel: { color: '#8fa9c8', fontSize: 10, rotate: 30 },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          axisLabel: { color: '#8fa9c8', fontSize: 11 },
          splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
        },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
        legend: { bottom: 0, textStyle: { color: '#8fa9c8', fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
        series: [
          {
            type: 'bar',
            name: '基准方案',
            data: carbonBenefitData.value.baselineData,
            barWidth: 10,
            itemStyle: { color: 'rgba(255,179,71,0.6)', borderRadius: [2, 2, 0, 0] },
          },
          {
            type: 'bar',
            name: '实际方案',
            data: carbonBenefitData.value.actualData,
            barWidth: 10,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#69e36f' }, { offset: 1, color: 'rgba(105,227,111,0.2)' }]), borderRadius: [2, 2, 0, 0] },
          },
        ],
      })
    } else if (activeTab.value === 'source') {
      chart.setOption({
        grid: { top: 10, right: 20, bottom: 24, left: 60 },
        xAxis: {
          type: 'value',
          max: 60,
          axisLine: { show: false },
          axisLabel: { color: '#8fa9c8', fontSize: 11, formatter: '{value}%' },
          splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
        },
        yAxis: {
          type: 'category',
          data: carbonSourceData.value.items.map((d: any) => d.name),
          axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
          axisLabel: { color: '#8fa9c8', fontSize: 12 },
          axisTick: { show: false },
        },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
        series: [
          {
            type: 'bar',
            data: carbonSourceData.value.items.map((d: any) => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
            barWidth: 16,
            label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11, formatter: '{c}%' },
          },
        ],
      })
    }
    return
  }

  if (key === 'MONTHLY') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 80 },
      xAxis: {
        type: 'value',
        max: 100,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11, formatter: '{value}%' },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: monthlyProgressData.value.groups.map((d: any) => d.label),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: monthlyProgressData.value.groups.map((d: any) => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 4, 4, 0] } })),
          barWidth: 16,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11, formatter: '{c}%' },
        },
      ],
    })
    return
  }

  if (key === 'E01') {
    const cat = e01Filter.value as keyof typeof e01TrendData
    const series: any[] = []

    if (cat === 'all') {
      e01AvailableCategories.value.forEach(availableCat => {
        if (availableCat.key === 'all') return
        const catName = availableCat.label
        const catColor = e01CatColors[availableCat.key] || themeColor.value
        const data = e01TrendData[availableCat.key as keyof typeof e01TrendData] as number[]
        series.push({
          id: `bar-${availableCat.key}`,
          type: 'bar',
          name: catName,
          data,
          barWidth: 12,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: catColor },
              { offset: 1, color: `${catColor}40` },
            ]),
            borderRadius: [2, 2, 0, 0],
          },
        })
      })
    } else {
      const catName = e01Categories.find(c => c.key === cat)?.label || ''
      const catColor = e01CatColors[cat] || themeColor.value
      series.push({
        id: `bar-${cat}`,
        type: 'bar',
        name: catName,
        data: e01TrendData[cat] as number[],
        barWidth: 16,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: catColor },
            { offset: 1, color: `${catColor}40` },
          ]),
          borderRadius: [2, 2, 0, 0],
        },
      })
    }

    chart.setOption({
      grid: { top: 20, right: 16, bottom: 28, left: 32 },
      xAxis: {
        type: 'category',
        data: e01TrendData.months,
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(5,18,38,0.92)',
        borderColor: 'rgba(0,174,255,0.3)',
        textStyle: { color: '#e8f3ff', fontSize: 12 }
      },
      legend: {
        show: cat === 'all' && series.length > 1,
        bottom: 0,
        textStyle: { color: '#8fa9c8', fontSize: 11 },
        itemWidth: 14,
        itemHeight: 8,
      },
      series,
    }, { replaceMerge: ['series', 'legend'] })
  } else if (key === 'E02') {
    const statusData = e02StatusData.value
    const maxValue = Math.max(...statusData.map(d => d.value), 1)
    const xAxisMax = Math.ceil(maxValue * 1.3)
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: xAxisMax,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: statusData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: statusData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'S02') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 5,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: s02TypeData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: s02TypeData.map(d => ({ value: d.value })),
          barWidth: 8,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: 'rgba(47,156,255,0.3)' },
              { offset: 1, color: '#2f9cff' },
            ]),
            borderRadius: [0, 4, 4, 0],
          },
        },
      ],
    })
  } else if (key === 'G02') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: g02BucketData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: g02BucketData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'E03') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: e03TypeData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: e03TypeData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'E04') {
    const range = e04TimeRange.value
    const months = range === '6m' ? e04TrendData.months6 : e04TrendData.months12
    const data = range === '6m' ? e04TrendData.data6 : e04TrendData.data12

    chart.setOption({
      grid: { top: 20, right: 20, bottom: 30, left: 45 },
      xAxis: {
        type: 'category',
        data: months,
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 0.25,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(5,18,38,0.92)',
        borderColor: 'rgba(0,174,255,0.3)',
        textStyle: { color: '#e8f3ff', fontSize: 12 },
        formatter: (params: any) => {
          const p = params[0]
          return `${p.name}<br/>碳排放强度: <strong>${p.value}</strong> tCO₂e/万元`
        }
      },
      series: [
        {
          type: 'line',
          name: '碳排放强度',
          data: data,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { color: '#69e36f', width: 2 },
          itemStyle: { color: '#69e36f', borderColor: '#02111f', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(105,227,111,0.3)' },
              { offset: 1, color: 'rgba(105,227,111,0)' },
            ]),
          },
        },
        {
          type: 'line',
          name: '目标值',
          data: Array(months.length).fill(e04TrendData.target),
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#ffb347', width: 1, type: 'dashed' },
        },
      ],
    })
  } else if (key === 'S01') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 60 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 6,
        axisLine: { show: false },
        axisLabel: { show: false },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: s01TimelineNodes.map(d => d.label),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: [1, 2, 2, 3, 2, 4].map((v, i) => ({
            value: v,
            itemStyle: {
              color: s01TimelineNodes[i].type === 'current' ? '#2f9cff' :
                     s01TimelineNodes[i].type === 'start' ? '#69e36f' :
                     s01TimelineNodes[i].type === 'special' ? '#ffb347' : '#2f9cff',
              borderRadius: [0, 3, 3, 0],
            },
          })),
          barWidth: 4,
        },
      ],
    })
  } else if (key === 'G04') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: g04ProblemData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: g04ProblemData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'S03') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: s03TypeData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: s03TypeData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'S04') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: s04TypeData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: s04TypeData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'G01') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 4,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: g01StatusData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: g01StatusData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  } else if (key === 'G03') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 80 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: g03StatusData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: g03StatusData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  }
}

function handleResize() {
  chart?.resize()
}

function handleOverlayClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

function handleDetailReserved() {
  // 预留，不跳转
}

function handleSupervise() {
  showSuperviseToast.value = true
  if (superviseTimer) {
    clearTimeout(superviseTimer)
  }
  superviseTimer = setTimeout(() => {
    showSuperviseToast.value = false
    superviseTimer = null
  }, 3000)
}

watch(e01Filter, () => {
  if (props.detail.key === 'E01') {
    updateChart()
  }
})

watch(s02Filter, () => {
  if (props.detail.key === 'S02') {
    updateChart()
  }
})

watch(e04TimeRange, () => {
  if (props.detail.key === 'E04') {
    updateChart()
  }
})

watch(() => props.detail.key, (newKey) => {
  if (newKey === 'CARBON') {
    activeTab.value = 'cumulative'
  } else if (newKey === 'MONTHLY') {
    activeTab.value = 'progress'
  }
})

watch(activeTab, () => {
  if (isTopicMode.value) {
    nextTick(() => {
      if (chartRef.value) {
        if (chart) {
          chart.dispose()
          chart = null
        }
        chart = echarts.init(chartRef.value)
        updateChart()
      }
    })
  }
})

watch(() => props.detail.key, () => {
  nextTick(() => {
    initChart()
    modalRef.value?.focus()
  })
})

onMounted(() => {
  nextTick(() => {
    initChart()
    window.addEventListener('resize', handleResize)
    modalRef.value?.focus()
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
  if (superviseTimer) {
    clearTimeout(superviseTimer)
    superviseTimer = null
  }
})
</script>

<template>
  <S01SafetyProductionModal v-if="detail.key === 'S01'" @close="emit('close')" />
  <div v-else class="kpi-modal-overlay" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="kpi-modal"
      :class="`theme-${detail.theme}`"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="`modal-title-${detail.key}`"
      tabindex="-1"
    >
      <!-- 标题栏 -->
      <div class="modal-header">
        <h2 :id="`modal-title-${detail.key}`" class="modal-title">
          <span class="title-key">{{ detail.key }}</span>
          <span class="title-name">{{ detail.fullName }}</span>
        </h2>
        <button class="modal-close" aria-label="关闭" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <!-- 专题标签页导航 -->
      <div v-if="isTopicMode" class="modal-tabs">
        <button
          v-for="tab in detail.tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 顶部摘要指标 -->
      <div class="modal-summary">
        <div
          v-for="(item, idx) in (detail.key === 'E02' ? e02SummaryCards : detail.summary)"
          :key="idx"
          class="summary-card"
          :class="{
            clickable: detail.key === 'E02' && idx >= 1,
            active: detail.key === 'E02' && e02TableFilter?.value === (item as any).filterValue,
          }"
          @click="detail.key === 'E02' && idx >= 1 && (item as any).filterField && e02ToggleFilter((item as any).filterField, (item as any).filterValue)"
        >
          <div class="summary-label">{{ item.label }}</div>
          <div class="summary-value-row">
            <span class="summary-value" :style="{ color: detail.key === 'E02' && item.label === '已逾期' && (item as any).value > 0 ? '#ff4f5e' : detail.key === 'E02' && item.label === '已逾期' ? themeColor : themeColor }">
              {{ item.value }}
            </span>
            <span v-if="item.unit" class="summary-unit">{{ item.unit }}</span>
          </div>
        </div>
      </div>

      <!-- E04 指标计算说明 -->
      <div v-if="detail.key === 'E04'" class="calc-explanation">
        <div class="calc-title">指标计算说明</div>
        <div class="calc-formula">
          <span class="calc-term">单位完成产值碳排放强度（tCO₂e/万元）</span>
          <span class="calc-operator">＝</span>
          <span class="calc-term">核算期施工活动碳排放量（tCO₂e）</span>
          <span class="calc-operator">÷</span>
          <span class="calc-term">同期完成产值（万元）</span>
        </div>
        <div class="calc-formula">
          <span class="calc-term">核算期施工活动碳排放量</span>
          <span class="calc-operator">＝</span>
          <span class="calc-term">Σ（施工活动数据 × 对应排放因子）</span>
        </div>
        <div class="calc-note">施工活动数据包括纳入当前核算边界的燃油消耗量、用电量及其他能源活动数据。</div>
      </div>

      <!-- 主内容区：左图右摘 -->
      <div class="modal-content">
        <div class="content-main">
          <div class="chart-section">
            <div class="chart-header">
              <span class="chart-title">{{
                detail.key === 'E04' ? (e04TimeRange === '6m' ? '近6个完整核算月碳排放强度趋势' : '近12个完整核算月碳排放强度趋势') :
                detail.key === 'CARBON' && activeTab === 'cumulative' ? '月度累计碳足迹趋势' :
                detail.key === 'CARBON' && activeTab === 'benefit' ? '基准方案与实际方案对比' :
                detail.key === 'CARBON' && activeTab === 'source' ? '排放来源构成' :
                detail.key === 'CARBON' && activeTab === 'cost' ? '成本影响分析' :
                detail.key === 'CARBON' && activeTab === 'measures' ? '主要低碳措施' :
                detail.key === 'MONTHLY' && activeTab === 'progress' ? 'E/S/G 各组准备进度' :
                detail.key === 'MONTHLY' && activeTab === 'chapters' ? '章节与成果清单' :
                detail.key === 'MONTHLY' && activeTab === 'gaps' ? '缺项与校核清单' :
                detail.chartTitle
              }}</span>
              <!-- E01 筛选 -->
              <div v-if="detail.key === 'E01'" class="chart-filters">
                <button
                  v-for="cat in e01AvailableCategories"
                  :key="cat.key"
                  class="filter-btn"
                  :class="{ active: e01Filter === cat.key }"
                  @click="e01Filter = cat.key"
                >
                  {{ cat.label }}
                </button>
              </div>
              <!-- S02 筛选 -->
              <div v-if="detail.key === 'S02'" class="chart-filters">
                <button
                  v-for="cat in s02Categories"
                  :key="cat.key"
                  class="filter-btn"
                  :class="{ active: s02Filter === cat.key }"
                  @click="s02Filter = cat.key"
                >
                  {{ cat.label }}
                </button>
              </div>
              <!-- E04 时间范围 -->
              <div v-if="detail.key === 'E04'" class="chart-filters">
                <button
                  v-for="range in e04TimeRanges"
                  :key="range.key"
                  class="filter-btn"
                  :class="{ active: e04TimeRange === range.key }"
                  @click="e04TimeRange = range.key"
                >
                  {{ range.label }}
                </button>
              </div>
              <!-- E01 图例 -->
              <div v-if="detail.key === 'E01' && e01Filter === 'all' && e01CompositionData.length > 1" class="chart-legend">
                <span v-for="item in e01CompositionData" :key="item.name" class="legend-item">
                  <i class="legend-dot" :style="{ background: item.color }"></i>{{ item.name }}
                </span>
              </div>
            </div>

            <!-- S02 路线图 -->
            <div v-if="detail.key === 'S02'" class="route-map-area">
              <svg viewBox="0 0 100 50" preserveAspectRatio="none" class="route-svg">
                <defs>
                  <radialGradient id="s02MapGlow" cx="50%" cy="50%" r="65%">
                    <stop offset="0%" stop-color="#0d2d4a" stop-opacity="0.9" />
                    <stop offset="100%" stop-color="#020b18" stop-opacity="0" />
                  </radialGradient>
                </defs>
                <rect width="100" height="50" fill="url(#s02MapGlow)" />
                <!-- 路线 -->
                <path
                  d="M 5 42 Q 20 36 35 30 T 65 22 T 95 16"
                  fill="none"
                  stroke="rgba(47,156,255,0.6)"
                  stroke-width="1"
                />
                <!-- 风险点 -->
                <g v-for="p in filteredS02RiskPoints" :key="p.id" class="risk-point">
                  <circle :cx="p.x" :cy="p.y" r="3" fill="none" :stroke="p.level === '重大' ? '#ff4f5e' : '#ffb347'" stroke-width="1" />
                  <text :x="p.x" :y="p.y - 5" text-anchor="middle" :fill="p.level === '重大' ? '#ff4f5e' : '#ffb347'" font-size="4" font-weight="700">{{ p.label }}</text>
                </g>
                <!-- 罗盘 -->
                <g transform="translate(92, 8)">
                  <circle r="4" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="0.3" />
                  <path d="M 0 -3.5 L 1 0 L 0 3.5 L -1 0 Z" fill="#ff4f5e" />
                  <text y="-5" text-anchor="middle" fill="#e8f3ff" font-size="3">N</text>
                </g>
              </svg>
              <!-- 图例 -->
              <div class="route-legend">
                <span class="legend-item"><i class="legend-dot major"></i>重大风险（1）</span>
                <span class="legend-item"><i class="legend-dot bigger"></i>较大风险（5）</span>
              </div>
            </div>

            <!-- E03 沿线工点示意图 -->
            <div v-else-if="detail.key === 'E03'" class="e03-route-area">
              <svg viewBox="0 0 100 50" preserveAspectRatio="none" class="route-svg">
                <defs>
                  <radialGradient id="e03MapGlow" cx="50%" cy="50%" r="65%">
                    <stop offset="0%" stop-color="#0d2d4a" stop-opacity="0.9" />
                    <stop offset="100%" stop-color="#020b18" stop-opacity="0" />
                  </radialGradient>
                </defs>
                <rect width="100" height="50" fill="url(#e03MapGlow)" />
                <path
                  d="M 5 42 Q 20 36 35 30 T 65 22 T 95 16"
                  fill="none"
                  stroke="rgba(105,227,111,0.6)"
                  stroke-width="1"
                />
                <g v-for="p in e03WorkPoints" :key="p.id" class="work-point">
                  <circle :cx="p.x" :cy="p.y" r="3" :fill="p.risk === 'high' ? '#ff4f5e' : '#69e36f'" />
                  <circle :cx="p.x" :cy="p.y" r="5" fill="none" :stroke="p.risk === 'high' ? '#ff4f5e' : '#69e36f'" stroke-width="0.5" />
                  <text :x="p.x" :y="p.y - 5" text-anchor="middle" :fill="p.risk === 'high' ? '#ff4f5e' : '#69e36f'" font-size="4" font-weight="700">{{ p.label }}</text>
                  <text :x="p.x" :y="p.y + 7" text-anchor="middle" fill="#8fa9c8" font-size="3">{{ p.count }}项</text>
                </g>
              </svg>
              <div class="route-legend">
                <span class="legend-item"><i class="legend-dot high"></i>高风险（2）</span>
                <span class="legend-item"><i class="legend-dot normal"></i>一般风险（3）</span>
              </div>
            </div>

            <!-- S01 时间轴和月度状态 -->
            <div v-else-if="detail.key === 'S01'" class="s01-content">
              <div class="s01-timeline">
                <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="timeline-svg">
                  <defs>
                    <linearGradient id="timelineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stop-color="#69e36f" />
                      <stop offset="60%" stop-color="#2f9cff" />
                      <stop offset="100%" stop-color="#2f9cff" />
                    </linearGradient>
                  </defs>
                  <!-- 时间轴线 -->
                  <path
                    d="M 8 30 L 92 30"
                    fill="none"
                    stroke="rgba(143,169,200,0.2)"
                    stroke-width="2"
                    stroke-dasharray="4 2"
                  />
                  <!-- 进度线 -->
                  <path
                    d="M 8 30 L 82 30"
                    fill="none"
                    stroke="url(#timelineGradient)"
                    stroke-width="3"
                    stroke-linecap="round"
                  />
                  <!-- 节点 -->
                  <g transform="translate(8, 30)">
                    <circle r="4" fill="#69e36f" />
                    <text y="-8" text-anchor="middle" fill="#69e36f" font-size="5" font-weight="700">起算</text>
                    <text y="12" text-anchor="middle" fill="#8fa9c8" font-size="4">2025-07-10</text>
                  </g>
                  <g transform="translate(23, 30)">
                    <circle r="3" fill="none" stroke="#2f9cff" stroke-width="1.5" />
                    <text y="-6" text-anchor="middle" fill="#8fa9c8" font-size="4">30天</text>
                  </g>
                  <g transform="translate(38, 30)">
                    <circle r="3" fill="none" stroke="#2f9cff" stroke-width="1.5" />
                    <text y="-6" text-anchor="middle" fill="#8fa9c8" font-size="4">60天</text>
                  </g>
                  <g transform="translate(53, 30)">
                    <rect x="-4" y="-4" width="8" height="8" fill="none" stroke="#ffb347" stroke-width="1.5" rx="1" />
                    <text y="-6" text-anchor="middle" fill="#ffb347" font-size="4">特殊期</text>
                  </g>
                  <g transform="translate(68, 30)">
                    <circle r="3" fill="none" stroke="#2f9cff" stroke-width="1.5" />
                    <text y="-6" text-anchor="middle" fill="#8fa9c8" font-size="4">90天</text>
                  </g>
                  <g transform="translate(82, 30)">
                    <circle r="5" fill="#2f9cff" />
                    <circle r="3" fill="#02111f" />
                    <text y="-10" text-anchor="middle" fill="#2f9cff" font-size="5" font-weight="700">368天</text>
                    <text y="12" text-anchor="middle" fill="#8fa9c8" font-size="4">当前</text>
                  </g>
                </svg>
              </div>
              <div class="s01-monthly">
                <div class="monthly-title">近12个月安全生产状态</div>
                <div class="monthly-grid">
                  <div v-for="m in s01MonthlyStatus" :key="m.month" class="month-item">
                    <div class="month-dot status-normal" />
                    <div class="month-label">{{ m.month }}</div>
                    <div class="month-status">{{ m.status }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- S04 沿线位置分布 -->
            <div v-else-if="detail.key === 'S04'" class="e03-route-area">
              <svg viewBox="0 0 100 50" preserveAspectRatio="none" class="route-svg">
                <defs>
                  <radialGradient id="s04MapGlow" cx="50%" cy="50%" r="65%">
                    <stop offset="0%" stop-color="#0d2d4a" stop-opacity="0.9" />
                    <stop offset="100%" stop-color="#020b18" stop-opacity="0" />
                  </radialGradient>
                </defs>
                <rect width="100" height="50" fill="url(#s04MapGlow)" />
                <path
                  d="M 5 42 Q 20 36 35 30 T 65 22 T 95 16"
                  fill="none"
                  stroke="rgba(47,156,255,0.6)"
                  stroke-width="1"
                />
                <g v-for="p in s04LocationPoints" :key="p.id" class="work-point">
                  <circle :cx="p.x" :cy="p.y" r="3" :fill="p.type === 'passage' ? '#2f9cff' : p.type === 'noise' ? '#ffb347' : '#a66cff'" />
                  <circle :cx="p.x" :cy="p.y" r="5" fill="none" :stroke="p.type === 'passage' ? '#2f9cff' : p.type === 'noise' ? '#ffb347' : '#a66cff'" stroke-width="0.5" />
                  <text :x="p.x" :y="p.y - 5" text-anchor="middle" :fill="p.type === 'passage' ? '#2f9cff' : p.type === 'noise' ? '#ffb347' : '#a66cff'" font-size="4" font-weight="700">{{ p.label }}</text>
                </g>
              </svg>
              <div class="route-legend">
                <span class="legend-item"><i class="legend-dot passage"></i>通行影响</span>
                <span class="legend-item"><i class="legend-dot noise"></i>施工扰民</span>
                <span class="legend-item"><i class="legend-dot land"></i>征地协调</span>
              </div>
            </div>

            <!-- E01 空状态 -->
            <div v-else-if="detail.key === 'E01' && !e01HasData" class="chart-empty-state">
              <div class="empty-icon">
                <ShieldCheck :size="48" />
              </div>
              <div class="empty-text">当前统计周期暂无环境监测超标数据</div>
            </div>

            <!-- ECharts 图表 -->
            <div v-else-if="!isTopicMode || (detail.key === 'CARBON' && ['cumulative', 'benefit', 'source'].includes(activeTab)) || (detail.key === 'MONTHLY' && activeTab === 'progress')" ref="chartRef" class="chart-container" />

            <!-- 碳足迹-成本影响 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'cost'" class="topic-text-content">
              <div class="topic-metric-grid">
                <div class="topic-metric-card">
                  <div class="topic-metric-label">低碳措施投入</div>
                  <div class="topic-metric-value" style="color: #ffb347">{{ carbonCostData.investment }}<span class="unit">万元</span></div>
                </div>
                <div class="topic-metric-card">
                  <div class="topic-metric-label">节约成本</div>
                  <div class="topic-metric-value" style="color: #69e36f">{{ carbonCostData.savings }}<span class="unit">万元</span></div>
                </div>
                <div class="topic-metric-card">
                  <div class="topic-metric-label">避免成本</div>
                  <div class="topic-metric-value" style="color: #2f9cff">{{ carbonCostData.avoidedCost }}<span class="unit">万元</span></div>
                </div>
              </div>
              <div class="topic-note">
                <div class="topic-note-title">测算口径</div>
                <div class="topic-note-text">{{ carbonCostData.caliber }}</div>
              </div>
              <div class="topic-note warning">
                <div class="topic-note-text">{{ carbonCostData.note }}</div>
              </div>
            </div>

            <!-- 碳足迹-主要措施 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'measures'" class="topic-measures-content">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th v-for="col in carbonMeasuresData.columns" :key="col.key" :style="{ width: col.width || 'auto' }">{{ col.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in carbonMeasuresData.list" :key="ri">
                    <td v-for="col in carbonMeasuresData.columns" :key="col.key">
                      <span v-if="col.key === 'status'" class="status-tag" :class="`tag-${detail.theme}`">{{ (row as any)[col.key] }}</span>
                      <span v-else>{{ (row as any)[col.key] }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 碳足迹-核算边界说明 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'cumulative'" class="topic-note" style="margin-top: 6px;">
              <div class="topic-note-title">核算边界</div>
              <div class="topic-note-text">{{ carbonCumulativeData.boundary }}</div>
            </div>

            <!-- 月报-章节清单（完整表格） -->
            <div v-if="detail.key === 'MONTHLY' && activeTab === 'chapters'" class="topic-text-content full-height-table">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th v-for="col in monthlyChaptersData.columns" :key="col.key" :style="{ width: col.width || 'auto' }">{{ col.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in monthlyChaptersData.list" :key="row.index">
                    <td>{{ row.index }}</td>
                    <td>{{ row.group }}</td>
                    <td>{{ row.name }}</td>
                    <td>{{ row.type }}</td>
                    <td :class="{ 'text-success': row.status === '已完成', 'text-warning': row.status === '编制中' || row.status === '待确认', 'text-danger': row.status === '待补充' }">{{ row.status }}</td>
                    <td>{{ row.owner }}</td>
                    <td>{{ row.person }}</td>
                    <td>{{ row.deadline }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 月报-缺项清单（完整表格） -->
            <div v-if="detail.key === 'MONTHLY' && activeTab === 'gaps'" class="topic-text-content full-height-table">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th v-for="col in detail.detailColumns" :key="col.key" :style="{ width: col.width || 'auto' }">{{ col.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in filteredMonthlyDetailData" :key="ri">
                    <td v-for="col in detail.detailColumns" :key="col.key" :class="{ 'text-warning': row[col.key] === '待补齐' || row[col.key] === '待确认' || row[col.key] === '异常', 'text-danger': row[col.key] === '已逾期' }">
                      {{ row[col.key] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 碳足迹-低碳增益公式 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'benefit'" class="topic-note" style="margin-top: 6px;">
              <div class="topic-note-title">核心公式</div>
              <div class="topic-note-text">{{ carbonBenefitData.formula }}</div>
              <div class="topic-note-text" style="margin-top: 4px; color: #ffb347;">{{ carbonBenefitData.note }}</div>
            </div>

            <!-- 月报-状态链（仅进度页显示） -->
            <div v-if="detail.key === 'MONTHLY' && activeTab === 'progress'" class="monthly-status-chain">
              <div
                v-for="node in monthlyStatusChain"
                :key="node.key"
                class="chain-node"
                :class="node.status"
              >
                <div class="chain-dot" />
                <div class="chain-label">{{ node.label }}</div>
              </div>
            </div>
          </div>

          <!-- 明细表格 -->
          <div class="detail-section" v-if="!(detail.key === 'CARBON' && ['cost', 'measures'].includes(activeTab)) && !(detail.key === 'MONTHLY' && ['chapters', 'gaps'].includes(activeTab))">
            <div class="detail-title">{{ detail.detailTitle }}</div>
            <div class="detail-table-wrapper">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th
                      v-for="col in detail.detailColumns"
                      :key="col.key"
                      :style="{ width: col.width || 'auto' }"
                    >
                      {{ col.label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <template v-if="(detail.key === 'S02' ? filteredS02DetailData : detail.key === 'E02' ? e02FilteredDetailData : detail.key === 'MONTHLY' ? filteredMonthlyDetailData : detail.detailData).length > 0">
                    <tr
                      v-for="(row, ri) in (detail.key === 'S02' ? filteredS02DetailData : detail.key === 'E02' ? e02FilteredDetailData : detail.key === 'MONTHLY' ? filteredMonthlyDetailData : detail.detailData)"
                      :key="ri"
                      :class="{ 'row-selected': (detail.key === 'E02' && e02SelectedRow === ri) || (detail.key === 'E04' && e04SelectedRow === ri) }"
                      @click="detail.key === 'E02' && e02HandleRowClick(ri); detail.key === 'E04' && e04HandleRowClick(ri)"
                    >
                      <td
                        v-for="col in detail.detailColumns"
                        :key="col.key"
                        :class="{
                          'text-danger': col.key === 'deadlineStatus'
                            ? getE02DeadlineStatus(row.deadline as string).type === 'overdue'
                            : typeof row[col.key] === 'string' && (row[col.key] as string).includes('逾期'),
                          'text-warning': col.key === 'deadlineStatus'
                            ? getE02DeadlineStatus(row.deadline as string).type === 'warning'
                            : (col.key === 'attention' && (row[col.key] as string) === '需关注') ||
                              (typeof row[col.key] === 'string' && ((row[col.key] as string).includes('剩余') || (row[col.key] as string).includes('临期') || (row[col.key] as string).includes('今日'))),
                          'text-success': col.key === 'deadlineStatus'
                            ? getE02DeadlineStatus(row.deadline as string).type === 'normal'
                            : (col.key === 'attention' && (row[col.key] as string) === '正常') ||
                              (typeof row[col.key] === 'string' && (row[col.key] as string) === '正常'),
                        }"
                      >
                        <span
                          v-if="col.key === 'status' || col.key === 'level' || col.key === 'retest'"
                          class="status-tag"
                          :class="(typeof row[col.key] === 'string' && (row[col.key] as string).includes('逾期')) ? 'tag-red' : `tag-${detail.theme}`"
                        >
                          {{ row[col.key] }}
                        </span>
                        <span v-else-if="col.key === 'deadlineStatus'">
                          {{ getE02DeadlineStatus(row.deadline as string).text }}
                        </span>
                        <span v-else-if="col.key === 'no'" class="mono-no">{{ row[col.key] }}</span>
                        <span v-else>{{ row[col.key] }}</span>
                      </td>
                    </tr>
                  </template>
                  <tr v-else>
                    <td :colspan="detail.detailColumns.length" class="no-data">
                      暂无符合条件的数据
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 右侧摘要 -->
        <div class="content-side">
          <!-- E01 重点结论 -->
          <template v-if="detail.key === 'E01'">
            <div class="side-section">
              <div class="side-title">重点结论</div>
              <div class="conclusion-grid">
                <div class="conclusion-card">
                  <div class="conclusion-label">扬尘</div>
                  <div class="conclusion-value" style="color: #69e36f">1<span class="unit">项</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">噪声</div>
                  <div class="conclusion-value" style="color: #2f9cff">1<span class="unit">项</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">连续超标</div>
                  <div class="conclusion-value" style="color: #ff4f5e">0<span class="unit"></span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">待复测</div>
                  <div class="conclusion-value" style="color: #ffb347">1<span class="unit"></span></div>
                </div>
              </div>
            </div>
            <div class="side-section">
              <div class="side-title">类别构成（项）</div>
              <div class="ring-wrap">
                <svg v-if="e01CompositionData.length > 0" viewBox="0 0 100 100" class="mini-ring">
                  <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="12" />
                  <circle
                    v-for="(item, idx) in e01CompositionData"
                    :key="item.name"
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    :stroke="item.color"
                    stroke-width="12"
                    :stroke-dasharray="`${(item.value / e01CompositionData.reduce((sum, i) => sum + i.value, 0)) * 238.7} 238.7`"
                    stroke-linecap="round"
                    :transform="`rotate(${-90 + (e01CompositionData.slice(0, idx).reduce((sum, i) => sum + i.value, 0) / e01CompositionData.reduce((sum, i) => sum + i.value, 0)) * 360} 50 50)`"
                  />
                  <text x="50" y="46" text-anchor="middle" fill="#e8f3ff" font-size="9" font-weight="700">合计</text>
                  <text x="50" y="58" text-anchor="middle" fill="#e8f3ff" font-size="12" font-weight="700">{{ e01CompositionData.reduce((sum, i) => sum + i.value, 0) }} 项次</text>
                </svg>
                <div v-if="e01CompositionData.length > 0" class="ring-legend">
                  <div v-for="item in e01CompositionData" :key="item.name" class="ring-legend-item">
                    <i class="dot" :style="{ background: item.color }"></i>{{ item.name }} <span class="num">{{ item.value }}（{{ Math.round((item.value / e01CompositionData.reduce((sum, i) => sum + i.value, 0)) * 100) }}%）</span>
                  </div>
                </div>
                <div v-else class="empty-hint">暂无有效数据</div>
              </div>
            </div>
          </template>

          <!-- E02 问题类型 -->
          <template v-else-if="detail.key === 'E02'">
            <div class="side-section">
              <div class="side-title">未闭环问题类型分布</div>
              <div class="type-bar-list">
                <div
                  v-for="t in e02TypeData"
                  :key="t.name"
                  class="type-bar-item"
                  :class="{ active: e02TableFilter?.field === 'category' && e02TableFilter?.value === t.name }"
                  style="cursor: pointer;"
                  @click="e02ToggleFilter('category', t.name)"
                >
                  <span class="type-label">{{ t.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${(t.value / Math.max(...e02TypeData.map(d => d.value), 1)) * 100}%`, background: '#69e36f' }" />
                  </div>
                  <span class="type-value">{{ t.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner" :class="{ 'green': e02OverdueCount === 0 }">
              <AlertTriangle :size="14" />
              <span>{{ e02OverdueMessage }}</span>
            </div>
          </template>

          <!-- S02 风险摘要 -->
          <template v-else-if="detail.key === 'S02'">
            <div class="side-section">
              <div class="side-title">风险类型分布（项）</div>
              <div class="type-bar-list">
                <div v-for="t in s02TypeData" :key="t.name" class="type-bar-item">
                  <span class="type-label">{{ t.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${(t.value / 2) * 100}%` }" />
                  </div>
                  <span class="type-value">{{ t.value }}</span>
                </div>
              </div>
            </div>
            <div class="side-section">
              <div class="side-title">风险治理关注点（项）</div>
              <div class="type-bar-list">
                <div v-for="t in s02ConcernData" :key="t.name" class="type-bar-item">
                  <span class="type-label">{{ t.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${(t.value / 1) * 100}%` }" />
                  </div>
                  <span class="type-value">{{ t.value }}</span>
                </div>
              </div>
            </div>
          </template>

          <!-- G02 预警摘要 -->
          <template v-else-if="detail.key === 'G02'">
            <div class="side-section">
              <div class="side-title">预警摘要</div>
              <div class="warning-list">
                <div v-for="w in g02WarningData" :key="w.name" class="warning-item">
                  <span class="warning-label">{{ w.name }}</span>
                  <span class="warning-value">{{ w.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner purple">
              <AlertTriangle :size="14" />
              <span>1项许可已逾期，1项影响施工活动</span>
            </div>
          </template>

          <!-- E03 水保风险摘要 -->
          <template v-else-if="detail.key === 'E03'">
            <div class="side-section">
              <div class="side-title">水土保持风险摘要</div>
              <div class="warning-list">
                <div v-for="w in e03RiskSummary" :key="w.name" class="warning-item">
                  <span class="warning-label">{{ w.name }}</span>
                  <span class="warning-value">{{ w.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>汛期高风险点 2 处，请重点关注</span>
            </div>
          </template>

          <!-- E04 标段对比 -->
          <template v-else-if="detail.key === 'E04'">
            <div class="side-section">
              <div class="side-title">2026年6月标段强度对比</div>
              <div class="type-bar-list">
                <div v-for="(s, idx) in e04SectionRanking" :key="s.name" class="type-bar-item">
                  <span class="type-label" :class="{ 'text-highlight': s.highlight }">{{ s.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :class="{ 'bar-warning': !s.normal }" :style="{ width: `${(s.value / 0.2) * 100}%` }" />
                  </div>
                  <span class="type-value" :class="{ 'text-warning': !s.normal }">{{ s.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>K61+800~K65+200 互通段强度较上月上升11.4%，建议重点关注</span>
            </div>
          </template>

          <!-- S01 计数规则 -->
          <template v-else-if="detail.key === 'S01'">
            <div class="side-section">
              <div class="side-title">计数规则摘要</div>
              <ul class="rule-list">
                <li v-for="(r, idx) in s01Rules" :key="idx">{{ r }}</li>
              </ul>
            </div>
          </template>

          <!-- G04 节点影响 -->
          <template v-else-if="detail.key === 'G04'">
            <div class="side-section">
              <div class="side-title">节点影响摘要（受影响关键节点数）</div>
              <div class="warning-list">
                <div v-for="w in g04NodeImpact" :key="w.name" class="warning-item">
                  <span class="warning-label">{{ w.name }}</span>
                  <span class="warning-value">{{ w.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner purple">
              <AlertTriangle :size="14" />
              <span>存在 4 项资料影响关键节点，请尽快补齐以保障流程推进</span>
            </div>
          </template>

          <!-- S03 风险等级 -->
          <template v-else-if="detail.key === 'S03'">
            <div class="side-section">
              <div class="side-title">纠纷风险等级（项）</div>
              <div class="type-bar-list">
                <div v-for="t in s03RiskData" :key="t.name" class="type-bar-item">
                  <span class="type-label">{{ t.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${(t.value / 2) * 100}%`, background: t.color }" />
                  </div>
                  <span class="type-value">{{ t.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>1项群体性风险（工资支付涉及12人），1项逾期</span>
            </div>
          </template>

          <!-- S04 来源与位置 -->
          <template v-else-if="detail.key === 'S04'">
            <div class="side-section">
              <div class="side-title">来源渠道分布</div>
              <div class="warning-list">
                <div class="warning-item">
                  <span class="warning-label">12345 转办</span>
                  <span class="warning-value">1</span>
                </div>
                <div class="warning-item">
                  <span class="warning-label">来电来访</span>
                  <span class="warning-value">1</span>
                </div>
                <div class="warning-item">
                  <span class="warning-label">现场协调</span>
                  <span class="warning-value">1</span>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>1项逾期，1项影响施工进度</span>
            </div>
          </template>

          <!-- G01 受影响节点 -->
          <template v-else-if="detail.key === 'G01'">
            <div class="side-section">
              <div class="side-title">受影响关键节点（个）</div>
              <div class="warning-list">
                <div v-for="w in g01NodeImpact" :key="w.name" class="warning-item">
                  <span class="warning-label">{{ w.name }}</span>
                  <span class="warning-value">{{ w.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner purple">
              <AlertTriangle :size="14" />
              <span>1项已逾期，2项临近关键节点</span>
            </div>
          </template>

          <!-- G03 检查来源 -->
          <template v-else-if="detail.key === 'G03'">
            <div class="side-section">
              <div class="side-title">检查来源分布（项）</div>
              <div class="type-bar-list">
                <div v-for="t in g03SourceData" :key="t.name" class="type-bar-item">
                  <span class="type-label">{{ t.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${(t.value / 2) * 100}%` }" />
                  </div>
                  <span class="type-value">{{ t.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner purple">
              <AlertTriangle :size="14" />
              <span>2项逾期整改，1项影响施工进度</span>
            </div>
          </template>

          <!-- 碳足迹 右侧摘要（仅累计/增益/来源页显示） -->
          <template v-else-if="detail.key === 'CARBON' && ['cumulative', 'benefit', 'source'].includes(activeTab)">
            <div class="side-section">
              <div class="side-title">累计减排量</div>
              <div class="conclusion-grid">
                <div class="conclusion-card">
                  <div class="conclusion-label">核算减排量</div>
                  <div class="conclusion-value" style="color: #69e36f">{{ carbonBenefitData.totalReduction }}<span class="unit">tCO₂e</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">减排率</div>
                  <div class="conclusion-value" style="color: #2f9cff">{{ carbonBenefitData.reductionRate }}<span class="unit">%</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">碳汇/抵消</div>
                  <div class="conclusion-value" style="color: #00e5ff">326<span class="unit">tCO₂e</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">净排放</div>
                  <div class="conclusion-value" style="color: #e8f3ff">12,530<span class="unit">tCO₂e</span></div>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>实际排放、低碳增益、碳汇/抵消量三者分开核算，不得合并</span>
            </div>
          </template>

          <!-- 月报 右侧摘要（仅进度/缺项页显示） -->
          <template v-else-if="detail.key === 'MONTHLY' && ['progress', 'gaps'].includes(activeTab)">
            <div class="side-section">
              <div class="side-title">待补与校核（按组别）</div>
              <div class="type-bar-list">
                <div v-for="g in monthlyProgressData.groups" :key="g.key" class="type-bar-item" style="cursor: pointer;" @click="monthlyGroupFilter = monthlyGroupFilter === g.key ? 'all' : g.key">
                  <span class="type-label">{{ g.label }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${g.value}%`, background: g.color }" />
                  </div>
                  <span class="type-value">{{ g.value }}%</span>
                </div>
              </div>
            </div>
            <div class="side-section">
              <div class="side-title">月报章节完成情况</div>
              <div class="warning-list">
                <div v-for="ch in monthlyChaptersData.list" :key="ch.name" class="warning-item">
                  <span class="warning-label">[{{ ch.group }}] {{ ch.name }}</span>
                  <span class="warning-value" :style="{ color: ch.status === '已完成' ? '#69e36f' : ch.status === '数据校核中' ? '#ffb347' : '#ff4f5e' }">{{ ch.status }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 底栏 -->
      <div class="modal-footer-info">
        <div class="footer-item">
          <FileCheck :size="12" />
          <span>数据来源：{{ (detail.dataSource || '').split(' ')[0] }}</span>
        </div>
        <div class="footer-item">
          <Clock :size="12" />
          <span>更新时间：{{ detail.updateTime }}</span>
        </div>
        <div v-if="detail.completeness" class="footer-item" :class="detail.completenessStatus">
          <ShieldCheck :size="12" />
          <span>{{ detail.completeness }}</span>
        </div>
        <div v-if="detail.isMock" class="footer-item mock-tag">
          原型示例数据
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="modal-actions">
        <button v-if="detail.key === 'E02'" class="btn btn-ghost" :disabled="e02SelectedRow === null" @click="handleDetailReserved" :title="e02SelectedRow === null ? '请先选择事项' : '查看事项详情'">
          查看事项详情
        </button>
        <button
          class="btn btn-primary"
          :style="detail.key === 'E02' || detail.key === 'E04' ? { background: '#2f9cff', borderColor: '#2f9cff' } : { background: themeColor, borderColor: themeColor }"
          :disabled="(detail.key === 'E02' && !e02CanSupervise) || (detail.key === 'E04' && !e04CanSupervise)"
          @click="handleSupervise"
        >
          发起督办
        </button>
        <button class="btn btn-outline" @click="emit('close')">
          关闭
        </button>
      </div>

      <!-- 督办提示 -->
      <Transition name="toast">
        <div v-if="showSuperviseToast" class="supervise-toast">
          <AlertTriangle :size="14" />
          <span>督办功能为原型预留，尚未接入业务流程</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.kpi-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 11, 24, 0.72);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.kpi-modal {
  width: 68vw;
  max-width: 1280px;
  height: 80vh;
  max-height: 80vh;
  background: linear-gradient(180deg, rgba(7, 22, 44, 0.96) 0%, rgba(5, 18, 38, 0.96) 100%);
  border: 1px solid transparent;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.25s ease;
  box-shadow:
    0 0 0 1px rgba(0, 174, 255, 0.3),
    0 20px 60px rgba(0, 0, 0, 0.6);

  &.theme-green {
    border-color: rgba(105, 227, 111, 0.4);
    box-shadow:
      0 0 0 1px rgba(105, 227, 111, 0.35),
      0 20px 60px rgba(0, 0, 0, 0.6);
  }
  &.theme-blue {
    box-shadow:
      0 0 0 1px rgba(47, 156, 255, 0.35),
      0 20px 60px rgba(0, 0, 0, 0.6);
  }
  &.theme-purple {
    box-shadow:
      0 0 0 1px rgba(166, 108, 255, 0.35),
      0 20px 60px rgba(0, 0, 0, 0.6);
  }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

// Header
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.12);
  flex-shrink: 0;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,0.4), transparent);
  }

  .modal-title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 10px;

    .title-key {
      font-family: var(--font-num);
      font-size: 26px;
      font-weight: 700;
      color: var(--text-main);
      opacity: 0.95;
    }
    .theme-green & .title-key { color: #69e36f; text-shadow: 0 0 8px rgba(105,227,111,0.4); }
    .theme-blue & .title-key { color: #2f9cff; text-shadow: 0 0 8px rgba(47,156,255,0.4); }
    .theme-purple & .title-key { color: #a66cff; text-shadow: 0 0 8px rgba(166,108,255,0.4); }
  }

  .modal-close {
    width: 32px;
    height: 32px;
    border-radius: 4px;
    border: 1px solid var(--border-faint);
    background: rgba(255, 255, 255, 0.03);
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;

    &:hover {
      color: var(--text-main);
      border-color: var(--border-blue-dim);
      background: rgba(255, 79, 94, 0.1);
    }
  }
}

// Summary
.modal-summary {
  display: flex;
  gap: 10px;
  padding: 12px 18px;
  flex-shrink: 0;

  .summary-card {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid var(--border-faint);
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.02);
    display: flex;
    flex-direction: column;
    gap: 4px;
    transition: border-color 0.2s ease, background 0.2s ease;

    .summary-label {
      font-size: 12px;
      color: var(--text-muted);
    }
    .summary-value-row {
      display: flex;
      align-items: baseline;
      gap: 4px;

      .summary-value {
        font-family: var(--font-num);
        font-size: 26px;
        font-weight: 700;
        text-shadow: 0 0 6px currentColor;
        line-height: 1;
      }
      .summary-unit {
        font-size: 11px;
        color: var(--text-muted);
      }
    }

    // E02 可点击指标卡
    &.clickable {
      cursor: pointer;

      &:hover {
        background: rgba(47, 156, 255, 0.06);
        border-color: rgba(47, 156, 255, 0.35);
      }
    }

    &.active {
      background: rgba(47, 156, 255, 0.1);
      border-color: rgba(47, 156, 255, 0.6);
      box-shadow: 0 0 8px rgba(47, 156, 255, 0.25);
    }
  }
}

// E04 指标计算说明
.calc-explanation {
  padding: 8px 18px;
  background: rgba(105, 227, 111, 0.04);
  border-top: 1px solid rgba(105, 227, 111, 0.15);
  border-bottom: 1px solid rgba(105, 227, 111, 0.15);

  .calc-title {
    font-size: 12px;
    color: #69e36f;
    font-weight: 500;
    margin-bottom: 6px;
  }

  .calc-formula {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--text-main);
    margin-bottom: 4px;
    flex-wrap: wrap;

    .calc-term {
      color: var(--text-main);
      font-weight: 500;
    }

    .calc-operator {
      color: #69e36f;
      font-weight: 600;
    }
  }

  .calc-note {
    font-size: 10px;
    color: var(--text-muted);
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px dashed rgba(143, 169, 200, 0.15);
  }
}

// Content
.modal-content {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 12px;
  padding: 0 18px 12px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.content-side {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
}

.chart-section {
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  min-height: 0;
  max-height: 55%;

  .chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }

  .chart-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-main);
  }

  .chart-filters {
    display: flex;
    gap: 4px;

    .filter-btn {
      padding: 3px 10px;
      font-size: 11px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-faint);
      border-radius: 3px;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;

      &:hover {
        color: var(--text-main);
        border-color: var(--border-blue-dim);
      }
      &.active {
        color: var(--text-main);
        border-color: var(--border-blue);
        background: rgba(0, 174, 255, 0.1);
      }
    }
  }

  .chart-legend {
    display: flex;
    gap: 10px;

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      color: var(--text-muted);

      .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.dust { background: #69e36f; }
        &.noise { background: #2f9cff; }
        &.line { width: 12px; height: 2px; background: #ffffff; border-radius: 0; }
      }
    }
  }
}

.chart-container {
  height: 160px;
  width: 100%;
  flex-shrink: 0;
  min-height: 0;
}

// S02 路线图
.route-map-area {
  position: relative;
  height: 200px;
  border-radius: 3px;
  overflow: hidden;
  background: #031020;

  .route-svg {
    width: 100%;
    height: 100%;
    display: block;
  }

  .route-legend {
    position: absolute;
    bottom: 8px;
    right: 10px;
    display: flex;
    gap: 12px;
    background: rgba(5, 18, 38, 0.8);
    padding: 4px 10px;
    border-radius: 3px;
    border: 1px solid var(--border-faint);

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      color: var(--text-muted);

      .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.major { background: #ff4f5e; }
        &.bigger { background: #ffb347; }
      }
    }
  }
}

.chart-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 12px;
  color: var(--text-muted);

  .empty-icon {
    opacity: 0.5;
  }

  .empty-text {
    font-size: 14px;
    font-weight: 600;
  }
}

.e03-route-area {
  position: relative;
  height: 200px;
  border-radius: 3px;
  overflow: hidden;
  background: #031020;

  .route-svg {
    width: 100%;
    height: 100%;
    display: block;
  }

  .route-legend {
    position: absolute;
    bottom: 8px;
    right: 10px;
    display: flex;
    gap: 12px;
    background: rgba(5, 18, 38, 0.8);
    padding: 4px 10px;
    border-radius: 3px;
    border: 1px solid var(--border-faint);

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      color: var(--text-muted);

      .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.high { background: #ff4f5e; }
        &.normal { background: #69e36f; }
        &.passage { background: #2f9cff; }
        &.noise-dot { background: #ffb347; }
        &.land { background: #a66cff; }
      }
    }
  }
}

// Detail table
.detail-section {
  flex: 1;
  min-height: 0;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;

  .detail-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-main);
    flex-shrink: 0;
  }

  .detail-table-wrapper {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    min-height: 0;

    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-track { background: transparent; }
    &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
  }

  .detail-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;

    th {
      position: sticky;
      top: 0;
      background: rgba(5, 18, 38, 0.95);
      color: var(--text-muted);
      font-weight: 500;
      text-align: left;
      padding: 6px 8px;
      border-bottom: 1px solid var(--border-faint);
      white-space: nowrap;
    }

    td {
      padding: 6px 8px;
      color: var(--text-main);
      border-bottom: 1px solid rgba(143, 169, 200, 0.06);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      transition: background 0.15s ease;
    }

    tr:hover td {
      background: rgba(0, 174, 255, 0.04);
    }

    // E02 行选中
    tr.row-selected td {
      background: rgba(47, 156, 255, 0.12) !important;
      box-shadow: inset 2px 0 0 #2f9cff;
    }

    .status-tag {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 2px;
      font-size: 10px;
      font-weight: 500;

      &.tag-green {
        color: #69e36f;
        background: rgba(105, 227, 111, 0.12);
        border: 1px solid rgba(105, 227, 111, 0.3);
      }
      &.tag-blue {
        color: #2f9cff;
        background: rgba(47, 156, 255, 0.12);
        border: 1px solid rgba(47, 156, 255, 0.3);
      }
      &.tag-purple {
        color: #a66cff;
        background: rgba(166, 108, 255, 0.12);
        border: 1px solid rgba(166, 108, 255, 0.3);
      }
      &.tag-red {
        color: #ff4f5e;
        background: rgba(255, 79, 94, 0.12);
        border: 1px solid rgba(255, 79, 94, 0.3);
      }
    }

    .mono-no {
      font-family: var(--font-num);
      font-size: 11px;
    }

    .text-danger { color: #ff4f5e; }
    .text-warning { color: #ffb347; }
    .text-success { color: #69e36f; }
    .no-data { text-align: center; color: var(--text-faint); padding: 20px; }
  }
}

// Side
.side-section {
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;

  .side-title {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-main);
    margin-bottom: 8px;
  }
}

.conclusion-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;

  .conclusion-card {
    padding: 8px;
    border: 1px solid var(--border-faint);
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.02);
    text-align: center;

    .conclusion-label {
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 2px;
    }
    .conclusion-value {
      font-family: var(--font-num);
      font-size: 18px;
      font-weight: 700;
      text-shadow: 0 0 4px currentColor;

      .unit {
        font-size: 10px;
        font-weight: 400;
        text-shadow: none;
        margin-left: 2px;
        color: var(--text-muted);
      }
    }
  }
}

.ring-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;

  .mini-ring {
    width: 100px;
    height: 100px;
  }

  .ring-legend {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 3px;

    .ring-legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 10px;
      color: var(--text-muted);

      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;

        &.green { background: #69e36f; }
        &.blue { background: #2f9cff; }
        &.purple { background: #a66cff; }
        &.cyan { background: #00e5ff; }
      }

      .num {
        margin-left: auto;
        color: var(--text-main);
        font-family: var(--font-num);
      }
    }
  }
}

.type-bar-list {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .type-bar-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 4px;
    border-radius: 3px;
    transition: background 0.2s ease;

    .type-label {
      font-size: 11px;
      color: var(--text-muted);
      width: 60px;
      flex-shrink: 0;
    }
    .type-bar-track {
      flex: 1;
      height: 5px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 3px;
      overflow: hidden;

      .type-bar-fill {
        height: 100%;
        background: #2f9cff;
        border-radius: 3px;
        transition: width 0.3s ease;
      }
    }
    .type-value {
      font-size: 11px;
      color: var(--text-main);
      width: 16px;
      text-align: right;
      font-family: var(--font-num);
    }

    // E02 类型筛选激活
    &.active {
      background: rgba(47, 156, 255, 0.12);
      box-shadow: inset 0 0 0 1px rgba(47, 156, 255, 0.5);

      .type-label {
        color: #2f9cff;
      }
    }
  }
}

.alert-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(255, 79, 94, 0.08);
  border: 1px solid rgba(255, 79, 94, 0.25);
  border-radius: 3px;
  font-size: 11px;
  color: #ff8a94;

  &.purple {
    background: rgba(166, 108, 255, 0.08);
    border-color: rgba(166, 108, 255, 0.25);
    color: #c79eff;
  }

  // E02 无逾期时的正常状态
  &.green {
    background: rgba(105, 227, 111, 0.08);
    border-color: rgba(105, 227, 111, 0.25);
    color: #69e36f;
  }
}

.warning-list {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .warning-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 8px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    font-size: 11px;

    .warning-label { color: var(--text-muted); }
    .warning-value {
      color: var(--text-main);
      font-family: var(--font-num);
      font-weight: 600;
    }
  }
}

// S01 时间轴和月度状态
.s01-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .s01-timeline {
    flex-shrink: 0;
    height: 100px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    border: 1px solid var(--border-faint);

    .timeline-svg {
      width: 100%;
      height: 100%;
      display: block;
    }
  }

  .s01-monthly {
    flex: 1;
    min-height: 0;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    border: 1px solid var(--border-faint);
    padding: 8px 10px;

    .monthly-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 6px;
    }

    .monthly-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 6px;
      height: calc(100% - 24px);
      overflow-y: auto;
      overflow-x: hidden;

      &::-webkit-scrollbar { width: 4px; }
      &::-webkit-scrollbar-track { background: transparent; }
      &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
    }

    .month-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      padding: 4px;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 2px;

      .month-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;

        &.status-normal { background: #69e36f; box-shadow: 0 0 4px rgba(105,227,111,0.4); }
        &.status-warning { background: #ffb347; box-shadow: 0 0 4px rgba(255,179,71,0.4); }
        &.status-danger { background: #ff4f5e; box-shadow: 0 0 4px rgba(255,79,94,0.4); }
      }

      .month-label {
        font-size: 9px;
        color: var(--text-muted);
        white-space: nowrap;
      }

      .month-status {
        font-size: 9px;
        color: #69e36f;
      }
    }
  }
}

// E04 高亮样式
.text-highlight {
  color: #69e36f !important;
  font-weight: 600;
}

.bar-warning {
  background: #ff4f5e !important;
}

// S01 规则列表
.rule-list {
  margin: 0;
  padding-left: 16px;
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.6;

  li {
    margin-bottom: 4px;

    &:last-child { margin-bottom: 0; }
  }
}

// Footer info
.modal-footer-info {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 18px;
  border-top: 1px solid rgba(143, 169, 200, 0.1);
  background: rgba(255, 255, 255, 0.01);
  flex-shrink: 0;
  font-size: 11px;
  color: var(--text-faint);

  .footer-item {
    display: flex;
    align-items: center;
    gap: 4px;

    &.complete { color: #69e36f; }
    &.incomplete { color: #ffb347; }
    &.pending { color: var(--text-faint); }
  }

  .mock-tag {
    margin-left: auto;
    padding: 2px 8px;
    background: rgba(255, 179, 71, 0.1);
    border: 1px solid rgba(255, 179, 71, 0.25);
    border-radius: 2px;
    color: #ffb347;
    font-size: 10px;
  }
}

// Actions
.modal-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 12px 18px 16px;
  flex-shrink: 0;

  .btn {
    padding: 8px 24px;
    font-size: 14px;
    font-weight: 500;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
    min-width: 140px;
    height: 36px;

    &:active:not(:disabled) {
      transform: scale(0.97);
      transition-duration: 0.08s;
    }

    &:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
  }
  .btn-ghost {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-faint);
    color: var(--text-muted);

    &:hover:not(:disabled) {
      border-color: var(--border-blue-dim);
      color: var(--text-main);
    }
  }
  .btn-primary {
    border: 1px solid;
    color: #02111f;
    font-weight: 600;

    &:hover:not(:disabled) { opacity: 0.9; }
  }
  .btn-outline {
    background: transparent;
    border: 1px solid var(--border-blue-dim);
    color: var(--text-main);

    &:hover {
      border-color: var(--border-blue);
      background: rgba(0, 174, 255, 0.06);
    }
  }
}

// 专题标签页
.modal-tabs {
  display: flex;
  gap: 4px;
  padding: 0 18px 10px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.08);
  flex-shrink: 0;

  .tab-btn {
    padding: 4px 14px;
    font-size: 12px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-faint);
    border-radius: 3px;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;

    &:hover {
      color: var(--text-main);
      border-color: var(--border-blue-dim);
    }

    &.active {
      color: var(--text-main);
      border-color: var(--border-blue);
      background: rgba(0, 174, 255, 0.1);
    }
  }
}

// 专题文本内容
.topic-text-content {
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);

  // 月报章节清单和缺项清单完整表格
  &.full-height-table {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;

    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-track { background: transparent; }
    &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }

    .detail-table {
      flex: 1;
      th { position: sticky; top: 0; }
    }
  }

  .topic-metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 10px;

    .topic-metric-card {
      padding: 10px;
      border: 1px solid var(--border-faint);
      border-radius: 3px;
      background: rgba(255, 255, 255, 0.02);
      text-align: center;

      .topic-metric-label {
        font-size: 11px;
        color: var(--text-muted);
        margin-bottom: 4px;
      }

      .topic-metric-value {
        font-family: var(--font-num);
        font-size: 20px;
        font-weight: 700;
        text-shadow: 0 0 4px currentColor;

        .unit {
          font-size: 10px;
          font-weight: 400;
          text-shadow: none;
          margin-left: 2px;
          color: var(--text-muted);
        }
      }
    }
  }

  .topic-note {
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    border: 1px solid var(--border-faint);
    margin-bottom: 6px;

    &.warning {
      border-color: rgba(255, 179, 71, 0.25);
      color: #ffb347;
    }

    .topic-note-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 4px;
    }

    .topic-note-text {
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.5;
    }
  }
}

// 专题措施内容
.topic-measures-content {
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;
  overflow-y: auto;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
}

// 月报状态链
.monthly-status-chain {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  flex-shrink: 0;

  .chain-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;

    &:not(:last-child)::after {
      content: '';
      position: absolute;
      top: 6px;
      right: -50%;
      width: 100%;
      height: 2px;
      background: rgba(143, 169, 200, 0.15);
    }

    &.done::after {
      background: #69e36f;
    }

    &.current::after {
      background: linear-gradient(90deg, #2f9cff, rgba(143, 169, 200, 0.15));
    }

    .chain-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(143, 169, 200, 0.2);
      margin-bottom: 6px;
      position: relative;
      z-index: 1;
    }

    &.done .chain-dot {
      background: #69e36f;
      box-shadow: 0 0 4px rgba(105, 227, 111, 0.4);
    }

    &.current .chain-dot {
      background: #2f9cff;
      box-shadow: 0 0 4px rgba(47, 156, 255, 0.4);
    }

    &.pending .chain-dot {
      background: rgba(143, 169, 200, 0.2);
    }

    .chain-label {
      font-size: 10px;
      color: var(--text-muted);
      white-space: nowrap;
    }

    &.done .chain-label { color: #69e36f; }
    &.current .chain-label { color: #2f9cff; font-weight: 600; }
  }
}

// ── Toast 过渡动画 ──
.toast-enter-active {
  transition: opacity 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.toast-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
