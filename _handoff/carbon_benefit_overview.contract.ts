export type CarbonDataNature = 'formal' | 'demo' | 'mixed'
export type CarbonSourceMode = 'mysql' | 'server-json' | 'frontend-mock'
export type CarbonSourceCode = 'diesel' | 'electricity' | 'material' | 'transport'
export type SegmentCode = 'SEG-01' | 'SEG-02' | 'SEG-03'
export type MaterialCode = 'cement' | 'steel' | 'asphalt'

export interface CarbonMonthlyEmission {
  month: string
  monthlyEmission: number
  cumulativeEmission: number
  emissionUnit: 'tCO₂e'
}

export interface CarbonSegmentItem {
  segmentCode: SegmentCode
  segmentName: string
  sortOrder: number
  activityAmount: number
  emissionAmount: number
  share: number
}

export interface CarbonSourceBreakdown {
  sourceCode: CarbonSourceCode
  sourceName: string
  sortOrder: number
  totalActivityAmount: number
  activityUnit: string
  emissionFactor: number | null
  factorUnit: string
  totalEmission: number
  emissionUnit: 'tCO₂e'
  share: number
  segments: CarbonSegmentItem[]
  dataNature: CarbonDataNature
  verificationStatus: string
  evidenceStatus: string
}

export interface CarbonMaterialItem {
  materialCode: MaterialCode
  materialName: string
  sortOrder: number
  activityAmount: number
  activityUnit: 't'
  factor: number
  factorUnit: string
  emissionAmount: number
}

export interface CarbonMaterialSegmentBreakdown {
  segmentCode: SegmentCode
  segmentName: string
  sortOrder: number
  materials: CarbonMaterialItem[]
  totalEmission: number
  emissionUnit: 'tCO₂e'
}

export interface CarbonCostSummary {
  investmentCost: number
  operatingCostSaving: number
  materialTransportDisposalSaving: number
  totalCostSaving: number
  netCostImpact: number
  currencyUnit: '万元'
  formula: string
  netCostFormula: string
  notice: string
}

export interface CarbonBenefitOverview {
  key: 'CARBON'
  monthlyEmissions: CarbonMonthlyEmission[]
  emissionSources: CarbonSourceBreakdown[]
  segmentBreakdown: CarbonSourceBreakdown[]
  materialSegmentBreakdown: CarbonMaterialSegmentBreakdown[]
  carbonCostLabel: '低碳措施节约成本'
  carbonCostValue: number
  carbonCostUnit: '万元'
  dataNotice: string
  costNotice: string
  sourceMode: CarbonSourceMode
  dataNature: CarbonDataNature
  verificationStatus: string
  evidenceStatus: string
  isMock: boolean
  topicData: {
    overview: Record<string, unknown>
    sources: Record<string, unknown>
    benefit: Record<string, unknown>
    measuresCosts: {
      measures: Array<Record<string, unknown>>
      costSummary: CarbonCostSummary
    }
  }
}
