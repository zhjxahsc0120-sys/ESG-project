import type { ChatSession, QuickCategory, ChatMessage, AssistantDataBasis } from '@/types/assistant'

export const quickCategories: QuickCategory[] = [
  { key: 'E', name: '环境 E', desc: '环境事项与指标查询', color: 'green', icon: 'E' },
  { key: 'S', name: '社会 S', desc: '安全与劳务事项查询', color: 'blue', icon: 'S' },
  { key: 'G', name: '治理 G', desc: '合规与治理事项查询', color: 'purple', icon: 'G' },
  { key: 'CARBON', name: '碳专题', desc: '碳排放与低碳措施', color: 'cyan', icon: 'C' },
  { key: 'MONTHLY', name: '月报专题', desc: '月报资料准备情况', color: 'orange', icon: 'M' },
]

export const recentSessions: ChatSession[] = [
  { id: '1', title: '当前有哪些未闭环环保问题？', lastTime: '今天', active: true },
  { id: '2', title: '项目累计碳排放是多少？', lastTime: '今天' },
  { id: '3', title: '本月月报资料待处理情况', lastTime: '昨天' },
  { id: '4', title: '当前有哪些逾期整改事项？', lastTime: '昨天' },
  { id: '5', title: '三标段安全风险情况', lastTime: '7月18日' },
]

export const welcomeQuestions = [
  '当前有哪些未闭环环保问题？',
  '当前较大及以上安全风险点有多少？',
  '项目累计碳排放是多少？',
  '本月还有哪些月报资料待处理？',
  '查看E/S/G三类指标总体情况',
]

export function createEnvIssuesAnswer(): ChatMessage {
  return {
    id: 'a1',
    role: 'assistant',
    content:
      '截至2026年7月20日，项目当前共有12项未闭环环保问题，其中整改中7项、待复查3项、待销项2项。',
    time: '2026-07-20 10:30:15',
    kpiCards: [
      { label: '未闭环问题总数', value: 12, unit: '项', color: 'blue' },
      { label: '整改中', value: 7, unit: '项', color: 'cyan' },
      { label: '待复查', value: 3, unit: '项', color: 'orange' },
      { label: '待销项', value: 2, unit: '项', color: 'red' },
    ],
    tableData: {
      title: '未闭环环保问题清单（前5条）',
      total: 12,
      columns: [
        { key: 'index', label: '序号', width: '6%', align: 'center' },
        { key: 'name', label: '问题名称', width: '28%', align: 'left' },
        { key: 'segment', label: '标段', width: '10%', align: 'center' },
        { key: 'dept', label: '责任部门', width: '14%', align: 'left' },
        { key: 'deadline', label: '截止日期', width: '14%', align: 'center' },
        { key: 'handleStatus', label: '办理状态', width: '10%', align: 'center' },
        { key: 'timeStatus', label: '时限状态', width: '10%', align: 'center' },
        { key: 'action', label: '关联页面', width: '8%', align: 'center' },
      ],
      rows: [
        {
          index: 1,
          name: 'K18+200弃渣场挡墙排水不畅',
          segment: '一标段',
          dept: '路基工程队',
          deadline: '2026-07-25',
          handleStatus: '整改中',
          timeStatus: '正常',
          action: '查看',
        },
        {
          index: 2,
          name: '二号拌合站扬尘治理措施不到位',
          segment: '二标段',
          dept: '拌合站管理组',
          deadline: '2026-07-22',
          handleStatus: '整改中',
          timeStatus: '临期',
          action: '查看',
        },
        {
          index: 3,
          name: '隧道出口污水处理设备故障',
          segment: '三标段',
          dept: '隧道工程队',
          deadline: '2026-07-18',
          handleStatus: '待复查',
          timeStatus: '逾期',
          action: '查看',
        },
        {
          index: 4,
          name: 'K32+500声屏障设置缺失',
          segment: '二标段',
          dept: '路面工程队',
          deadline: '2026-07-28',
          handleStatus: '整改中',
          timeStatus: '正常',
          action: '查看',
        },
        {
          index: 5,
          name: '取土场生态恢复方案待审批',
          segment: '一标段',
          dept: '工程技术部',
          deadline: '2026-07-20',
          handleStatus: '待销项',
          timeStatus: '临期',
          action: '查看',
        },
      ],
      viewAllText: '查看全部12项',
    },
    dataBasis: {
      itemName: '未闭环环保问题',
      scope: '罗宜高速项目全线',
      updateTime: '2026-07-20 10:30',
      dataPeriod: '截至2026年7月20日',
      verifyStatus: '已核验',
      stableId: 'E02-ENV-ISSUES-202607',
      sources: [
        { name: '施工月报（2026年6月）', time: '2026-07-05', status: '已关联' },
        { name: '监理月报（2026年6月）', time: '2026-07-08', status: '已关联' },
        { name: '监理通知单', time: '2026-07-12', status: '已关联' },
        { name: '环保检查通报', time: '2026-07-15', status: '已关联' },
        { name: '第三方检测报告', time: '2026-07-10', status: '已关联' },
      ],
      caliber:
        '未闭环环保问题，是指已发现但尚未完成整改、复查或销项的环境环保事项。统计范围包括施工期扬尘、噪声、污水、固废、生态保护等方面的问题。',
    },
    followUps: [
      '查看逾期事项',
      '按责任部门统计',
      '查看三标段问题',
      '导出问题清单',
    ],
  }
}

export function getEmptyAcceptanceSession(): ChatMessage[] {
  const userMsg: ChatMessage = {
    id: 'u1',
    role: 'user',
    content: '当前有哪些未闭环环保问题？',
    time: '2026-07-20 10:30:00',
  }
  return [userMsg, createEnvIssuesAnswer()]
}
