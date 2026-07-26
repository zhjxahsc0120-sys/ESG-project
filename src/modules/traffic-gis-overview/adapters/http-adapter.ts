import type {
  BusinessLinksResponse,
  RelationsResponse,
  TrafficDataAdapter,
  TrafficLayerDefinition,
  TrafficMapContext,
  TrafficMapFeature,
} from "../types";
export interface GisResponse<T> {
  code: number;
  data: T;
  meta?: {
    dataSource?: string;
    dataNature?: string;
  };
}
export class HttpTrafficAdapter implements TrafficDataAdapter {
  private lastMeta?: { dataSource?: string; dataNature?: string };
  constructor(
    private readonly baseUrl = import.meta.env.VITE_TRAFFIC_API_BASE ||
      "/api/esg/gis",
  ) {}
  getLastMeta() {
    return this.lastMeta;
  }
  async getLayers(context: TrafficMapContext) {
    const result = await this.request<TrafficLayerDefinition[]>("/layers", { ...context });
    return result.data;
  }
  async getFeatures(layer: TrafficLayerDefinition, context: TrafficMapContext) {
    const result = await this.request<TrafficMapFeature[]>("/features", {
      ...context,
      layerId: layer.id,
    });
    return result.data;
  }
  async getRelations(feature: TrafficMapFeature, context: TrafficMapContext) {
    return this.request<RelationsResponse>(
      `/features/${feature.id}/relations`,
      { projectId: context.projectId },
    ).then((r) => r.data);
  }
  async getBusinessLinks(feature: TrafficMapFeature, context: TrafficMapContext) {
    return this.request<BusinessLinksResponse>(
      `/features/${feature.id}/business-links`,
      { projectId: context.projectId },
    ).then((r) => r.data);
  }
  private async request<T>(path: string, params: Record<string, unknown>) {
    const query = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v != null)
        .map(([k, v]) => [k, String(v)]),
    );
    const response = await fetch(this.baseUrl + path + "?" + query);
    if (!response.ok) throw new Error("GIS接口失败 " + response.status);
    const body = (await response.json()) as GisResponse<T>;
    if (body.code !== 0) throw new Error("GIS接口返回失败");
    this.lastMeta = body.meta;
    return body;
  }
}
