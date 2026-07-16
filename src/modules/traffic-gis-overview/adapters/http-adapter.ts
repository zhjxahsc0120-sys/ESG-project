import type {
  TrafficDataAdapter,
  TrafficLayerDefinition,
  TrafficMapContext,
  TrafficMapFeature,
} from "../types";
export class HttpTrafficAdapter implements TrafficDataAdapter {
  constructor(
    private readonly baseUrl = import.meta.env.VITE_TRAFFIC_API_BASE ||
      "/api/esg/gis",
  ) {}
  async getLayers(context: TrafficMapContext) {
    return this.request<TrafficLayerDefinition[]>("/layers", { ...context });
  }
  async getFeatures(layer: TrafficLayerDefinition, context: TrafficMapContext) {
    return this.request<TrafficMapFeature[]>("/features", {
      ...context,
      layerId: layer.id,
    });
  }
  private async request<T>(path: string, params: Record<string, unknown>) {
    const query = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v != null)
        .map(([k, v]) => [k, String(v)]),
    );
    const response = await fetch(this.baseUrl + path + "?" + query);
    if (!response.ok) throw new Error("GIS接口失败 " + response.status);
    const body = (await response.json()) as { code: number; data: T };
    if (body.code !== 0) throw new Error("GIS接口返回失败");
    return body.data;
  }
}
