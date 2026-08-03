/**
 * 首页驾驶舱 KPI 正式名称目录（V1.0 现场调研优化）
 * 仅改口径文案与追溯元数据，不改卡片布局。
 */
export const KPI_HOME_CATALOG = {
  E01: {
    label: '环境影响事件',
    fullName: '环境影响事件',
    unit: '项',
    source: 'E01 监测超标/异常事件台账',
    caliber: '覆盖环境监测异常、水质/噪声异常及污染类事件（当前统计初检有效超标项次）',
  },
  E02: {
    label: '未闭环环境问题',
    fullName: '未闭环环境问题',
    unit: '项',
    source: 'E02 环保问题台账 + E03 水保问题台账',
    caliber: '未闭环环保问题与未闭环水保问题合计（不含已闭环/已撤销/已合并）',
  },
  E03: {
    label: '生态保护事项',
    fullName: '生态保护事项',
    unit: '项',
    source: '水保/生态相关问题台账',
    caliber: '弃土场、临时用地、表土剥离、复垦、边坡复绿、生态敏感区等事项',
  },
  E04: {
    label: '项目累计碳排放',
    fullName: '项目累计碳排放',
    unit: 'tCO₂e',
    source: 'E04 碳排放活动台账',
    caliber: '保持原核算逻辑',
  },
  S01: {
    label: '连续安全生产天数',
    fullName: '连续安全生产天数',
    unit: '天',
    source: 'S01 确认批次',
    caliber: '保持原逻辑',
  },
  S02: {
    label: '重大风险源管控',
    fullName: '重大风险源管控',
    unit: '项',
    source: 'S02 安全风险点台账',
    caliber: '在管重大/较大风险源（未销号）',
  },
  S03: {
    label: '农民工权益保障',
    fullName: '农民工权益保障',
    unit: '项',
    source: '劳务纠纷/工资支付台账',
    caliber: '未办结劳务权益相关事项（工资、纠纷等）',
  },
  S04: {
    label: '群众诉求闭环',
    fullName: '群众诉求闭环',
    unit: '项',
    source: '群众诉求台账',
    caliber: '未办结投诉、信访、征拆协调等诉求',
  },
  G01: {
    label: '合规审批事项',
    fullName: '合规审批事项',
    unit: '项',
    source: '法定报批报建/合规手续台账',
    caliber: '未完成合规审批手续事项',
  },
  G02: {
    label: '合规问题闭环',
    fullName: '合规问题闭环',
    unit: '项',
    source: '检查整改事项台账',
    caliber: '未关闭整改事项',
  },
  G03: {
    label: '参建单位履约评价',
    fullName: '参建单位履约评价',
    unit: '',
    source: '履约评价台账（待建）',
    caliber: '单位排名/履约评价/考核结果；台账未接入前首页展示「待评价」，不编造',
  },
  G04: {
    label: '治理内控风险',
    fullName: '治理内控风险',
    unit: '项',
    source: '许可台账 + 关键合规资料缺口台账',
    caliber: '临期/逾期许可与待补齐关键合规资料合计（廉洁内控待独立台账接入）',
  },
} as const

export type KpiHomeCode = keyof typeof KPI_HOME_CATALOG
