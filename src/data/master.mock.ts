// ─────────────────────────────────────────────
// 母版 mock 数据（/ui-master/dashboard 专用）
// 所有数值与状态均为 mock，不代表正式业务结论。
// 12 项 KPI 名称严格使用项目已确认的 E01~E04 / S01~S04 / G01~G04 正式名称。
// ─────────────────────────────────────────────

export type MasterKpiTheme = 'green' | 'blue' | 'purple'

export interface MasterKpiItem {
  key: string
  label: string         // 精简名称，用于首页卡片显示
  fullName: string       // 完整正式指标名称，用于弹窗/详情/Tooltip
  value: string | number
  unit: string
}

export interface MasterKpiGroup {
  key: 'E' | 'S' | 'G'
  title: string
  letter: string
  theme: MasterKpiTheme
  items: MasterKpiItem[]
}

export interface MasterNavItem {
  key: string
  label: string
}

export interface MasterTimelineStep {
  index: number
  label: string
  status: 'completed' | 'active' | 'pending'
}

export const masterNavItems: MasterNavItem[] = [
  { key: 'dashboard', label: '工作台首页' },
  { key: 'compliance', label: '合规底线管理' },
  { key: 'carbon', label: '碳足迹与低碳增益' },
  { key: 'risk', label: '风险预警与督办' },
  { key: 'gis', label: '项目现场一张图' },
  { key: 'monthly', label: '月报管理' },
  { key: 'documents', label: '资料与档案' },
]

export const masterKpiGroups: MasterKpiGroup[] = [
  {
    key: 'E',
    title: '环境环保组',
    letter: 'E',
    theme: 'green',
    items: [
      { key: 'E01', label: '环境监测超标项次', fullName: '环境监测超标项次', value: 2, unit: '项次' },
      { key: 'E02', label: '未闭环环保问题', fullName: '当前未闭环环保问题事项数', value: 5, unit: '项' },
      { key: 'E03', label: '未闭环水保问题', fullName: '当前未闭环水土保持问题事项数', value: 7, unit: '项' },
      { key: 'E04', label: '项目累计碳排放', fullName: '项目累计碳排放', value: 6175, unit: 'tCO₂e' },
    ],
  },
  {
    key: 'S',
    title: '社会责任组',
    letter: 'S',
    theme: 'blue',
    items: [
      { key: 'S01', label: '连续安全生产天数', fullName: '连续安全生产天数', value: 368, unit: '天' },
      { key: 'S02', label: '在管较大及以上安全风险点', fullName: '当前在管较大及以上安全风险点数', value: 6, unit: '项' },
      { key: 'S03', label: '未办结劳务用工纠纷', fullName: '当前未办结劳务用工纠纷事项数', value: 2, unit: '项' },
      { key: 'S04', label: '未办结群众诉求', fullName: '当前未办结群众诉求事项数', value: 3, unit: '项' },
    ],
  },
  {
    key: 'G',
    title: '治理合规组',
    letter: 'G',
    theme: 'purple',
    items: [
      { key: 'G01', label: '未完成报批报建', fullName: '当前未完成法定报批报建事项数', value: 5, unit: '项' },
      { key: 'G02', label: '许可临期及逾期', fullName: '当前临期及逾期许可事项数', value: 5, unit: '项' },
      { key: 'G03', label: '未关闭检查整改', fullName: '当前未关闭检查整改事项数', value: 6, unit: '项' },
      { key: 'G04', label: '待补齐合规资料', fullName: '当前待补齐关键合规资料项数', value: 4, unit: '项' },
    ],
  },
]

export const masterTimelineSteps: MasterTimelineStep[] = [
  { index: 1, label: '前期研究', status: 'completed' },
  { index: 2, label: '勘察设计', status: 'completed' },
  { index: 3, label: '用地与专项手续', status: 'completed' },
  { index: 4, label: '招投标与合同', status: 'completed' },
  { index: 5, label: '施工准备', status: 'completed' },
  { index: 6, label: '路基桥涵施工', status: 'active' },
  { index: 7, label: '路面交安机电房建', status: 'pending' },
  { index: 8, label: '环保水保恢复', status: 'pending' },
  { index: 9, label: '交工验收', status: 'pending' },
  { index: 10, label: '试运营', status: 'pending' },
  { index: 11, label: '竣工验收/审计/移交', status: 'pending' },
]

// ─────────────────────────────────────────────
// 第二阶段：右栏三面板 + 时间轴 mock 数据
// ─────────────────────────────────────────────

// ── 合规保障与风险防控成效 ──
export interface ComplianceMetric {
  key: string
  label: string
  value: number
  unit: string
}

export interface ComplianceBarItem {
  name: string
  value: number
  unit: string
  ratio: number  // 0~100，控制进度条长度
}

export interface ComplianceFocusItem {
  title: string
  statusLabel: string  // 简短状态文字
  status: 'normal' | 'warning' | 'danger'
}

export const complianceMetrics: ComplianceMetric[] = [
  { key: 'cm1', label: '合规点位', value: 12, unit: '个' },
  { key: 'cm2', label: '碳排点位', value: 6, unit: '个' },
  { key: 'cm3', label: '敏感区', value: 3, unit: '处' },
  { key: 'cm4', label: '风险点', value: 6, unit: '处' },
]

export const complianceBars: ComplianceBarItem[] = [
  { name: '报批报建完成', value: 18, unit: '项', ratio: 82 },
  { name: '许可手续办理', value: 12, unit: '项', ratio: 65 },
  { name: '整改事项关闭', value: 15, unit: '项', ratio: 71 },
  { name: '资料归档', value: 8, unit: '项', ratio: 48 },
]

export const complianceFocus: ComplianceFocusItem[] = [
  { title: 'K37大桥施工许可续期', statusLabel: '临期预警', status: 'warning' },
  { title: '2号取土场水土保持整改', statusLabel: '整改中', status: 'normal' },
  { title: '隧道施工噪声超标未闭环', statusLabel: '督办中', status: 'danger' },
]

// ── 碳足迹与低碳增益 ──
export interface CarbonMetric {
  key: string
  label: string
  value: string | number
  unit: string
  note?: string  // 测算口径/非财务确认结论等提示
}

export interface CarbonSource {
  name: string
  value: number  // 百分比
  color: string
}

export interface CarbonMeasure {
  name: string
  ratio: number     // 0~100，进度条长度
  level: '高' | '较高' | '中' | '低'
}

export const carbonMetrics: CarbonMetric[] = [
  { key: 'cc1', label: '项目累计碳排放', value: 6175, unit: 'tCO₂e' },
  { key: 'cc2', label: '累计核算减排量', value: 1445, unit: 'tCO₂e' },
  { key: 'cc3', label: '低碳措施成本影响', value: 0, unit: '万元', note: '非财务确认结论' },
]

export const carbonSources: CarbonSource[] = [
  { name: '施工用油', value: 42, color: '#1687ff' },
  { name: '施工用电', value: 28, color: '#43d36b' },
  { name: '主要材料', value: 22, color: '#8b5cf6' },
  { name: '其他', value: 8, color: '#ff9f2f' },
]

export const carbonMeasures: CarbonMeasure[] = [
  { name: '电动设备替代燃油设备', ratio: 88, level: '高' },
  { name: '光伏供电系统应用', ratio: 72, level: '较高' },
  { name: '施工废料回收利用', ratio: 55, level: '中' },
  { name: '拌合站余热回收', ratio: 38, level: '中' },
]

// ── 月报准备与输出 ──
export interface MonthlySummary {
  month: string
  completionRate: number   // 0~100
  pendingDocs: number
  pendingConfirm: number
  status: string
  expectedDate: string
}

export interface MonthlyDocItem {
  name: string
  dept: string
  deadline: string
  status: 'pending' | 'urgent'
}

export const monthlySummary: MonthlySummary = {
  month: '2026年7月',
  completionRate: 82,
  pendingDocs: 6,
  pendingConfirm: 4,
  status: '报告编制',
  expectedDate: '7月12日',
}

export const monthlyDocs: MonthlyDocItem[] = [
  { name: '噪声监测原始记录', dept: '安全环保部', deadline: '7月15日', status: 'urgent' },
  { name: '碳排放因子确认', dept: '技术管理部', deadline: '7月14日', status: 'urgent' },
  { name: '安全检查记录归档', dept: '安全环保部', deadline: '7月16日', status: 'pending' },
  { name: '安全数据核验', dept: '工程管理部', deadline: '7月16日', status: 'pending' },
  { name: '临时用地批复复印件', dept: '工程管理部', deadline: '7月15日', status: 'urgent' },
]
