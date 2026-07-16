export type FeatureStatus =
  "normal" | "attention" | "warning" | "critical" | "offline";
export interface PointGeometry {
  type: "Point";
  coordinates: number[];
}
export interface LineGeometry {
  type: "LineString";
  coordinates: number[][];
}
export interface PolygonGeometry {
  type: "Polygon";
  coordinates: number[][][];
}
export type TrafficGeometry = PointGeometry | LineGeometry | PolygonGeometry;
export interface TrafficMapFeature {
  id: string;
  layerId: string;
  objectType: string;
  name: string;
  geometry: TrafficGeometry;
  properties: Record<string, unknown>;
  status?: FeatureStatus;
  riskLevel?: 1 | 2 | 3 | 4;
  updatedAt?: string;
}
export interface TrafficMapContext {
  projectId: string;
  sectionId?: string;
  currentTime?: string | Date;
  visibleLayerIds?: string[];
}
export interface TrafficLayerStyle {
  color: string;
  width?: number;
  opacity?: number;
  outlineColor?: string;
  icon?: string;
  showLabel?: boolean;
  labelColor?: string;
  labelSize?: number;
  labelField?: string;
}
export interface TrafficLayerDefinition {
  id: string;
  name: string;
  geometryType: "point" | "line" | "polygon" | "tileset";
  enabled: boolean;
  source: { type: "mock" | "api" | "geojson" | "tileset"; url?: string };
  style: TrafficLayerStyle;
  objectType?: string;
  featureCount?: number;
  fields?: string[];
  minCameraHeight?: number;
  maxCameraHeight?: number;
  zIndex?: number;
}
export interface TrafficDataAdapter {
  getLayers(context: TrafficMapContext): Promise<TrafficLayerDefinition[]>;
  getFeatures(
    layer: TrafficLayerDefinition,
    context: TrafficMapContext,
  ): Promise<TrafficMapFeature[]>;
  getFeatureDetail?(
    feature: TrafficMapFeature,
  ): Promise<Record<string, unknown>>;
}
export interface InitialView {
  longitude: number;
  latitude: number;
  height: number;
  heading?: number;
  pitch?: number;
  roll?: number;
}
export interface TrafficGisOverviewProps {
  projectId: string;
  sectionId?: string;
  currentTime?: string | Date;
  visibleLayerIds?: string[];
  selectedFeatureId?: string;
  initialView?: InitialView;
  showLegend?: boolean;
  showModeSwitch?: boolean;
  interactionEnabled?: boolean;
  dataMode?: "mock" | "api" | "shp";
}
