<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import * as Cesium from "cesium";
import TrafficLegend from "./TrafficLegend.vue";
import FeatureCard from "./FeatureCard.vue";
import BusinessLinksPanel from "./BusinessLinksPanel.vue";
import LayerControl from "./LayerControl.vue";
import MapChrome from "./MapChrome.vue";
import { ViewerManager } from "../cesium/core/ViewerManager";
import { CameraManager } from "../cesium/core/CameraManager";
import { LayerRegistry } from "../cesium/layers/LayerRegistry";
import { BasemapManager } from "../cesium/layers/BasemapManager";
import { SpatialAssetManager } from "../cesium/layers/SpatialAssetManager";
import { defaultBasemapId, type BasemapId } from "../config/basemaps.config";
import {
  VectorLayerStore,
  parseGeoJson,
  type VectorLayerRecord,
} from "../vector/VectorLayerStore";
import {
  SpatialAssetStore,
  type SpatialAssetRecord,
  type SpatialAssetType,
} from "../assets/SpatialAssetStore";
import { PointRenderer } from "../cesium/renderers/PointRenderer";
import { PolylineRenderer } from "../cesium/renderers/PolylineRenderer";
import { PolygonRenderer } from "../cesium/renderers/PolygonRenderer";
import { PickManager } from "../cesium/interaction/PickManager";
import { HighlightManager } from "../cesium/interaction/HighlightManager";
import {
  MockTrafficAdapter,
  HttpTrafficAdapter,
  ShpTrafficAdapter,
} from "../adapters";
import type {
  BusinessLinksResponse,
  FeatureRelation,
  GisBusinessLinkOpenPayload,
  PresentationMode,
  TrafficGisOverviewProps,
  TrafficLayerDefinition,
  TrafficLayerStyle,
  TrafficMapContext,
  TrafficMapFeature,
  E01MapMarker,
} from "../types";
import { trafficGisConfig } from "../config/traffic-gis.config";
import {
  LABEL_ATLAS_SCALE,
  crispLabelFont,
  sectionColors,
  tokens,
  wholePx,
} from "../config/style-tokens";
import { CoordinateAdapter } from "../cesium/core/CoordinateAdapter";
import { featureColor } from "../cesium/renderers/render-utils";

const props = withDefaults(defineProps<TrafficGisOverviewProps>(), {
  showLegend: true,
  showModeSwitch: true,
  showConfigButton: true,
  interactionEnabled: true,
  dataMode: "mock",
  presentationMode: "preview" as PresentationMode,
  e01Active: false,
  e01Markers: () => [],
  e01SelectedEventId: null,
  e01SelectedPointId: null,
  e01ShowInfoCard: false,
  e02Active: false,
  e02SelectedFeatureId: null,
  e03Active: false,
  e03SelectedFeatureId: null,
  s02Active: false,
  s02SelectedFeatureId: null,
});

const emit = defineEmits<{
  ready: [{ viewerReady: true }];
  featureClick: [TrafficMapFeature];
  featureHover: [TrafficMapFeature | null];
  statsChange: [
    { visibleFeatureCount: number; warningCount: number; offlineCount: number },
  ];
  error: [{ layerId?: string; message: string; recoverable: boolean }];
  openKpiSource: [payload: GisBusinessLinkOpenPayload];
  e01EventSelect: [eventId: number];
  e01PointSelect: [pointId: number];
  e02FeatureSelect: [featureId: string];
  e02MapBlankClick: [];
  e03FeatureSelect: [featureId: string];
  e03MapBlankClick: [];
  s02FeatureSelect: [featureId: string];
  s02MapBlankClick: [];
  cameraMove: [];
}>();

const root = ref<HTMLElement>();
const canvas = ref<HTMLElement>();
const loading = ref(true);
  const selected = ref<TrafficMapFeature | null>(null);
  const relationsData = ref<FeatureRelation[]>([]);
  const relationsLoading = ref(false);
  const businessLinksData = ref<BusinessLinksResponse | null>(null);
  const businessLinksLoading = ref(false);
  const businessLinksOpen = ref(false);
  const compassHeading = ref(0);
  const scope = ref<"all" | "section-1" | "section-2" | "section-3">("all");
  const layerGroup = ref<"all" | "basic" | "environment" | "social" | "governance" | "situation">("all");
  /** E01 环境监测点（水质/扬尘/噪声超标点 overlay）显隐 */
  const showMonitors = ref(true);
  /** S02 安全风险点显隐 / 强调 */
  const showRiskPoints = ref(true);
  const panelOpen = ref(false);

/**
 * S02 安全风险点空间落点（与 mysql_api._S02_GIS_LINKS / seed_s02_risk_display_v0_2 对齐）：
 * - S02-001 → slope-1-1
 * - S02-002 → section-2-1
 * - S02-003/004 → section-3-1
 * - S02-005 → waste-1-1
 * - S02-006 → slope-2-1 (+ section-3-1 辅)
 * - S02-009/010 → section-1-1 (+ eco-1-1 辅于 010)
 */
const S02_FEATURE_IDS = new Set([
  "section-1-1",
  "section-2-1",
  "section-3-1",
  "slope-1-1",
  "slope-2-1",
  "waste-1-1",
  "eco-1-1",
]);

function sectionKeyToCn(sectionKey: string): string {
  const map: Record<string, string> = {
    "section-1": "1标段",
    "section-2": "2标段",
    "section-3": "3标段",
  };
  return map[sectionKey] || sectionKey;
}

/** 是否为 S02 关联空间对象（含 risk-point 图层类型，若有） */
function isS02RiskFeature(feature: TrafficMapFeature | undefined | null): boolean {
  if (!feature) return false;
  if (feature.objectType === "risk-point") return true;
  return S02_FEATURE_IDS.has(feature.id);
}

function isRiskLayer(layer: TrafficLayerDefinition) {
  return layer.objectType === "risk-point";
}
  const activeBasemap = ref<BasemapId>(defaultBasemapId);
  const availableLayers = ref<TrafficLayerDefinition[]>([]);
  const visibleIds = ref<string[]>([]);
  const vectorLayers = ref<VectorLayerRecord[]>([]);
  const assets = ref<SpatialAssetRecord[]>([]);
  const isDemoData = ref(false);

const vectorStore = new VectorLayerStore();
const assetStore = new SpatialAssetStore();
const manager = new ViewerManager();
const registry = new LayerRegistry();
const highlighter = new HighlightManager();

let basemaps: BasemapManager | undefined;
let spatialAssets: SpatialAssetManager | undefined;
let camera: CameraManager | undefined;
let picker: PickManager | undefined;
let resizeObserver: ResizeObserver | undefined;
let removeCameraChanged: (() => void) | undefined;
let loadVersion = 0;
let e01DataSource: Cesium.CustomDataSource | undefined;
let savedCameraView: ReturnType<CameraManager["captureView"]> | null = null;
let savedScope: typeof scope.value | null = null;
let savedLayerGroup: typeof layerGroup.value | null = null;

const pointRenderer = new PointRenderer();
const lineRenderer = new PolylineRenderer();
const polygonRenderer = new PolygonRenderer();
const shpAdapter = new ShpTrafficAdapter();

const adapter = computed(() =>
  props.dataMode === "api"
    ? new HttpTrafficAdapter()
    : props.dataMode === "shp"
      ? shpAdapter
      : new MockTrafficAdapter(),
);

const STYLE_STORAGE_KEY = "traffic-esg-business-layer-styles-v2";

function savedStyles() {
  try {
    // 清理旧版缓存，避免历史绿色样式残留
    localStorage.removeItem("traffic-esg-business-layer-styles-v1");
    return JSON.parse(
      localStorage.getItem(STYLE_STORAGE_KEY) || "{}",
    ) as Record<string, Partial<TrafficLayerStyle>>;
  } catch {
    return {};
  }
}

const context = (): TrafficMapContext => ({
  projectId: props.projectId,
  sectionId: props.sectionId,
  currentTime: props.currentTime,
  visibleLayerIds: visibleIds.value,
});

function filterLayer(layer: TrafficLayerDefinition) {
    const type = layer.objectType || "";

    // 快捷开关：S02 安全风险点图层（objectType=risk-point）；E01 监测点走 e01 overlay，不滤 SHP
    if (isRiskLayer(layer) && !showRiskPoints.value) {
      return false;
    }

    if (layerGroup.value === "all" || layerGroup.value === "situation") {
      return true;
    }
    const groupMap: Record<string, string[]> = {
      basic: ["road-section", "chainage"],
      environment: ["water-source", "ecological-zone", "spoil-site", "slope-monitor"],
      // S 社会：S02 风险点 + 作为 S02 落点的边坡监测点
      social: ["risk-point", "slope-monitor"],
      governance: [],
      situation: [],
    };
    const allowedTypes = groupMap[layerGroup.value] || [];
    if (!allowedTypes.includes(type)) return false;
    return true;
  }

/**
 * 安全风险点关：隐藏 S02 挂接的点状落点（如 slope-2-1）；
 * 标段线（section-*-1）保留为底图，仅去掉强调（见 applyRiskEmphasis）。
 */
function filterFeaturesForOverlays(
  _layer: TrafficLayerDefinition,
  features: TrafficMapFeature[],
) {
  if (showRiskPoints.value) return features;
  return features.filter((f) => {
    if (!isS02RiskFeature(f)) return true;
    // 底图标段线不因 S02 开关整段消失
    return f.objectType === "road-section";
  });
}

async function renderLayer(
  layer: TrafficLayerDefinition,
  features: TrafficMapFeature[],
) {
  const viewer = manager.get();
  if (layer.geometryType === "point")
    return pointRenderer.render(viewer, layer, features, props.presentationMode);
  if (layer.geometryType === "line")
    return lineRenderer.render(viewer, layer, features, props.presentationMode);
  if (layer.geometryType === "polygon")
    return polygonRenderer.render(viewer, layer, features, props.presentationMode);
  return [];
}

async function loadDefinitions() {
    const layers = await adapter.value.getLayers({
      ...context(),
      visibleLayerIds: undefined,
    });
    if (adapter.value instanceof HttpTrafficAdapter) {
      const meta = adapter.value.getLastMeta();
      isDemoData.value = meta?.dataSource === "fallback" && meta?.dataNature === "demo";
    }
    const overrides = savedStyles();
    availableLayers.value = layers.map((layer) => {
      const sectionColor = sectionColors[layer.id as keyof typeof sectionColors];
      const forced = sectionColor
        ? {
            color: sectionColor,
            width: 5,
            labelSize: 15,
            labelColor: "#ffffff",
            showLabel: true,
          }
        : {};
      const merged = { ...layer.style, ...overrides[layer.id], ...forced };
      const type = layer.objectType || "";
      const minLabel =
        type === "water-source"
          ? 14
          : type === "ecological-zone" || type === "spoil-site"
            ? 13
            : type === "slope-monitor" || type === "risk-point"
              ? 13
              : 0;
      const style =
        minLabel > 0
          ? { ...merged, labelSize: Math.max(merged.labelSize || 0, minLabel) }
          : merged;
      return {
        ...layer,
        style,
      };
    });
    if (!visibleIds.value.length)
      visibleIds.value = props.visibleLayerIds?.length
        ? [...props.visibleLayerIds]
        : layers.filter((l) => l.enabled).map((l) => l.id);
  }

async function load() {
  const version = ++loadVersion;
  loading.value = true;
  const viewer = manager.get();
  registry.clear(viewer);
  try {
    if (!availableLayers.value.length) await loadDefinitions();
    for (const vector of vectorLayers.value.filter((item) => item.visible))
      registry.set(
        vector.id,
        await renderLayer(vector.definition, vector.features),
      );
    let layers = availableLayers.value.filter((l) =>
      visibleIds.value.includes(l.id),
    );
    layers = layers.filter(filterLayer);
    let count = 0,
      warning = 0,
      offline = 0;
    for (const layer of layers) {
      try {
        const rawFeatures = await adapter.value.getFeatures(layer, context());
        const features = filterFeaturesForOverlays(layer, rawFeatures);
        if (version !== loadVersion) return;
        registry.set(layer.id, await renderLayer(layer, features));
        count += features.length;
        warning += features.filter(
          (f) => f.status === "warning" || f.status === "critical",
        ).length;
        offline += features.filter((f) => f.status === "offline").length;
      } catch (e) {
        emit("error", {
          layerId: layer.id,
          message: e instanceof Error ? e.message : "图层加载失败",
          recoverable: true,
        });
      }
    }
    applyRiskEmphasis(showRiskPoints.value);
    emit("statsChange", {
      visibleFeatureCount: count,
      warningCount: warning,
      offlineCount: offline,
    });
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "地图数据加载失败",
      recoverable: true,
    });
  } finally {
    if (version === loadVersion) loading.value = false;
  }
}

async function syncAssets() {
  try {
    await spatialAssets?.sync(assets.value);
  } catch (e) {
    emit("error", {
      message:
        e instanceof Error
          ? e.message
          : "空间资源加载失败，请检查 URL 和跨域设置",
      recoverable: true,
    });
  }
}

async function switchBasemap(id: BasemapId) {
  try {
    basemaps?.switchTo(id);
    activeBasemap.value = id;
    await syncAssets();
    selected.value = null;
    relationsData.value = [];
    businessLinksData.value = null;
    businessLinksOpen.value = false;
    await load();
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "底图切换失败",
      recoverable: true,
    });
  }
}

function toggleLayer(id: string, show: boolean) {
  visibleIds.value = show
    ? [...new Set([...visibleIds.value, id])]
    : visibleIds.value.filter((item) => item !== id);
  load();
}

async function styleLayer(id: string, style: Partial<TrafficLayerStyle>) {
  availableLayers.value = availableLayers.value.map((layer) =>
    layer.id === id ? { ...layer, style: { ...layer.style, ...style } } : layer,
  );
  const overrides = savedStyles();
  localStorage.setItem(
    STYLE_STORAGE_KEY,
    JSON.stringify({ ...overrides, [id]: { ...overrides[id], ...style } }),
  );
  await load();
}

async function addVector(file: File) {
  try {
    const record = parseGeoJson(
      await file.text(),
      file.name.replace(/\.(geojson|json)$/i, ""),
    );
    vectorLayers.value = vectorStore.add(vectorLayers.value, record);
    await load();
    await locateVector(record.id);
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "矢量文件读取失败",
      recoverable: true,
    });
  }
}

async function toggleVector(id: string, visible: boolean) {
  vectorLayers.value = vectorLayers.value.map((item) =>
    item.id === id ? { ...item, visible } : item,
  );
  vectorStore.save(vectorLayers.value);
  await load();
}

async function styleVector(id: string, style: Partial<TrafficLayerStyle>) {
  vectorLayers.value = vectorLayers.value.map((item) =>
    item.id === id
      ? {
          ...item,
          color: String(style.color || item.color),
          definition: {
            ...item.definition,
            style: { ...item.definition.style, ...style },
          },
        }
      : item,
  );
  vectorStore.save(vectorLayers.value);
  await load();
}

async function removeVector(id: string) {
  registry.remove(id, manager.get());
  vectorLayers.value = vectorStore.remove(vectorLayers.value, id);
}

async function locateVector(id: string) {
  const entities = registry.get(id);
  if (entities.length) await camera?.flyTo(entities);
}

async function addAsset(input: {
  name: string;
  type: SpatialAssetType;
  url: string;
}) {
  assets.value = assetStore.add(assets.value, {
    ...input,
    visible: true,
    opacity: 1,
  });
  await syncAssets();
}

async function toggleAsset(id: string, visible: boolean) {
  assets.value = assets.value.map((item) =>
    item.id === id ? { ...item, visible } : item,
  );
  assetStore.save(assets.value);
  await syncAssets();
}

async function removeAsset(id: string) {
  assets.value = assetStore.remove(assets.value, id);
  await syncAssets();
}

async function locateAsset(id: string) {
  await spatialAssets?.locate(id);
}

async function refreshData() {
  availableLayers.value = [];
  await loadDefinitions();
  await load();
}

function featureOf(e: Cesium.Entity) {
  return e.properties?.trafficFeature?.getValue(Cesium.JulianDate.now()) as
    TrafficMapFeature | undefined;
}

function findEntity(id: string) {
  return registry.all().find((e) => featureOf(e)?.id === id);
}

async function flyToFeature(id: string, options?: { range?: number }) {
  const focus = featureFocusLngLat(id);
  if (focus) {
    const entity = findEntity(id);
    const feature = entity ? featureOf(entity) : undefined;
    const defaultRange =
      feature?.objectType === "road-section"
        ? 8500
        : feature?.objectType === "slope-monitor"
          ? 4200
          : 4800;
    camera?.flyToLonLat(focus.lon, focus.lat, options?.range ?? defaultRange);
    return;
  }
  const e = findEntity(id);
  if (e) await camera?.flyTo([e]);
}

function findEntityWithPosition(id: string) {
  return registry
    .all()
    .find((e) => featureOf(e)?.id === id && Boolean(e.position));
}

function featureFocusLngLat(id: string): { lon: number; lat: number } | null {
  try {
    const entity = findEntityWithPosition(id) || findEntity(id);
    if (!entity) return null;
    const now = Cesium.JulianDate.now();
    let cartesian: Cesium.Cartesian3 | undefined;
    if (entity.position) {
      cartesian = entity.position.getValue(now) as Cesium.Cartesian3 | undefined;
    }
    if (!cartesian && entity.polyline) {
      const positions = entity.polyline.positions?.getValue(now) as
        | Cesium.Cartesian3[]
        | undefined;
      if (positions?.length) {
        cartesian = positions[Math.floor(positions.length / 2)];
      }
    }
    if (!cartesian) return null;
    const carto = Cesium.Cartographic.fromCartesian(cartesian);
    return {
      lon: Cesium.Math.toDegrees(carto.longitude),
      lat: Cesium.Math.toDegrees(carto.latitude),
    };
  } catch {
    return null;
  }
}

function legendKeyForFeature(feature?: TrafficMapFeature | null): string | null {
  if (!feature) return null;
  if (feature.objectType === "water-source") return "water";
  if (feature.objectType === "ecological-zone") return "eco";
  if (feature.objectType === "spoil-site") return "spoil";
  if (feature.objectType === "slope-monitor") return "slope";
  if (feature.objectType === "road-section") {
    if (feature.id.startsWith("section-1")) return "s1";
    if (feature.id.startsWith("section-2")) return "s2";
    if (feature.id.startsWith("section-3")) return "s3";
  }
  return null;
}

const e02LegendHighlightKey = computed(() => {
  if (!props.e02Active || !props.e02SelectedFeatureId) return null;
  const entity = findEntity(props.e02SelectedFeatureId);
  return legendKeyForFeature(entity ? featureOf(entity) : null);
});

/** 要素中心在地图根节点坐标系下的屏幕点（调试/扩展用） */
function getFeatureScreenPoint(id: string): { x: number; y: number } | null {
  try {
    const viewer = manager.get();
    const entity = findEntityWithPosition(id) || findEntity(id);
    if (!entity) return null;
    const now = Cesium.JulianDate.now();
    let cartesian: Cesium.Cartesian3 | undefined;
    if (entity.position) {
      cartesian = entity.position.getValue(now) as Cesium.Cartesian3 | undefined;
    }
    if (!cartesian && entity.polyline) {
      const positions = entity.polyline.positions?.getValue(now) as
        | Cesium.Cartesian3[]
        | undefined;
      if (positions?.length) {
        cartesian = positions[Math.floor(positions.length / 2)];
      }
    }
    if (!cartesian) return null;
    const windowPos = Cesium.SceneTransforms.worldToWindowCoordinates(
      viewer.scene,
      cartesian,
    );
    if (!windowPos) return null;
    const canvasEl = viewer.scene.canvas;
    const canvasRect = canvasEl.getBoundingClientRect();
    const rootRect = root.value?.getBoundingClientRect();
    if (!rootRect) {
      return { x: windowPos.x, y: windowPos.y };
    }
    const scaleX = canvasRect.width / canvasEl.clientWidth;
    const scaleY = canvasRect.height / canvasEl.clientHeight;
    return {
      x: canvasRect.left - rootRect.left + windowPos.x * scaleX,
      y: canvasRect.top - rootRect.top + windowPos.y * scaleY,
    };
  } catch {
    return null;
  }
}

type PolylineVisualBackup = {
  width?: number;
  material?: Cesium.MaterialProperty | Cesium.Color;
  billboardScale?: number;
  polygonMaterial?: Cesium.MaterialProperty | Cesium.Color;
};

const e02VisualBackup = new Map<string, PolylineVisualBackup>();

function restoreE02SelectionVisual() {
  for (const entity of registry.all()) {
    const key = String(entity.id);
    const backup = e02VisualBackup.get(key);
    if (!backup) continue;
    if (backup.width != null && entity.polyline) {
      entity.polyline.width = new Cesium.ConstantProperty(backup.width);
    }
    if (backup.material != null && entity.polyline) {
      entity.polyline.material = backup.material as Cesium.MaterialProperty;
    }
    if (backup.billboardScale != null && entity.billboard) {
      entity.billboard.scale = new Cesium.ConstantProperty(backup.billboardScale);
    }
    if (backup.polygonMaterial != null && entity.polygon) {
      entity.polygon.material = backup.polygonMaterial as Cesium.MaterialProperty;
    }
  }
  e02VisualBackup.clear();
}

/** E02：选中本体加粗提亮 + 标签放大；其余关联略淡，非关联更淡 */
function applyE02SelectionVisual(
  selectedId: string | null,
  relatedIds: string[] = [],
) {
  restoreE02SelectionVisual();
  if (!selectedId && !relatedIds.length) return;
  const related = new Set(relatedIds.length ? relatedIds : selectedId ? [selectedId] : []);
  for (const entity of registry.all()) {
    const feature = featureOf(entity);
    if (!feature) continue;
    // 跳过光晕副实体，避免选中时线宽叠加倍增
    if (String(entity.id).endsWith("-glow")) continue;

    const key = String(entity.id);
    const backup: PolylineVisualBackup = {};
    if (entity.polyline) {
      const widthProp = entity.polyline.width;
      backup.width =
        typeof widthProp?.getValue === "function"
          ? Number(widthProp.getValue(Cesium.JulianDate.now()))
          : Number(widthProp) || 4;
      backup.material = entity.polyline.material as Cesium.MaterialProperty;
    }
    if (entity.billboard) {
      const scaleProp = entity.billboard.scale;
      backup.billboardScale =
        typeof scaleProp?.getValue === "function"
          ? Number(scaleProp.getValue(Cesium.JulianDate.now()) ?? 1)
          : Number(scaleProp) || 1;
    }
    if (entity.polygon) {
      backup.polygonMaterial = entity.polygon.material as Cesium.MaterialProperty;
    }
    e02VisualBackup.set(key, backup);

    const isSelected = feature.id === selectedId;
    const isRelated = related.has(feature.id);
    const sectionKey = feature.id.replace(/-\d+$/, "") as keyof typeof sectionColors;
    const fallback =
      sectionColors[sectionKey]
      || sectionColors[feature.id as keyof typeof sectionColors]
      || tokens.cyan;
    const base = featureColor(feature, fallback);

    if (isSelected) {
      if (entity.polyline) {
        const bump = feature.objectType === "road-section" ? 1.5 : 2.5;
        entity.polyline.width = new Cesium.ConstantProperty(
          Math.max((backup.width || 3) + bump, 5),
        );
        entity.polyline.material = new Cesium.ColorMaterialProperty(base.withAlpha(1));
      }
      if (entity.billboard) {
        entity.billboard.scale = new Cesium.ConstantProperty(1.35);
      }
      if (entity.polygon) {
        entity.polygon.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.55));
      }
    } else if (isRelated) {
      if (entity.polyline) {
        entity.polyline.width = new Cesium.ConstantProperty(backup.width || 3);
        entity.polyline.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.55));
      }
      if (entity.billboard) {
        entity.billboard.scale = new Cesium.ConstantProperty(1);
      }
    } else {
      if (entity.polyline) {
        entity.polyline.width = new Cesium.ConstantProperty(
          Math.max((backup.width || 3) - 0.5, 2),
        );
        entity.polyline.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.2));
      }
      if (entity.billboard) {
        entity.billboard.scale = new Cesium.ConstantProperty(0.85);
      }
      if (entity.polygon) {
        entity.polygon.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.12));
      }
    }
  }
}

async function flyToSection(sectionId: string) {
  if (!sectionId || sectionId === "all") {
    resetView();
    return;
  }
  const cn = sectionKeyToCn(sectionId);
  const entities = registry.all().filter((e) => {
    const f = featureOf(e);
    if (!f) return false;
    if (String(e.id).endsWith("-glow")) return false;
    // 优先飞入该标段走廊线
    if (
      f.objectType === "road-section" &&
      (f.layerId === sectionId ||
        f.id.startsWith(`${sectionId}-`) ||
        f.name === cn ||
        f.name === sectionId)
    ) {
      return true;
    }
    const sid = String(f.properties?.sectionId || "");
    return sid === sectionId || sid === cn;
  });
  const corridor = entities.filter(
    (e) => featureOf(e)?.objectType === "road-section",
  );
  const target = corridor.length ? corridor : entities;
  if (target.length) {
    await camera?.flyTo(target);
    return;
  }
  // 图层尚未渲染时，按标段中点兜底
  await flyToFeature(`${sectionId}-1`, { range: 8500 });
}

const riskVisualBackup = new Map<
  string,
  { billboardScale?: number; pointSize?: number }
>();

function restoreRiskEmphasis() {
  for (const entity of registry.all()) {
    const key = String(entity.id);
    const backup = riskVisualBackup.get(key);
    if (!backup) continue;
    if (backup.billboardScale != null && entity.billboard) {
      entity.billboard.scale = new Cesium.ConstantProperty(backup.billboardScale);
    }
    if (backup.pointSize != null && entity.point) {
      entity.point.pixelSize = new Cesium.ConstantProperty(backup.pointSize);
    }
  }
  riskVisualBackup.clear();
}

/** S02 安全风险点：对关联空间对象轻微放大，便于辨认 */
function applyRiskEmphasis(enabled: boolean) {
  restoreRiskEmphasis();
  if (!enabled) return;
  try {
    for (const entity of registry.all()) {
      if (String(entity.id).endsWith("-glow")) continue;
      const feature = featureOf(entity);
      if (!isS02RiskFeature(feature)) continue;
      const key = String(entity.id);
      const backup: { billboardScale?: number; pointSize?: number } = {};
      if (entity.billboard) {
        const scaleProp = entity.billboard.scale;
        backup.billboardScale =
          typeof scaleProp?.getValue === "function"
            ? Number(scaleProp.getValue(Cesium.JulianDate.now()) ?? 1)
            : Number(scaleProp) || 1;
        entity.billboard.scale = new Cesium.ConstantProperty(
          Math.max(backup.billboardScale * 1.28, 1.2),
        );
      }
      if (entity.point) {
        const sizeProp = entity.point.pixelSize;
        backup.pointSize =
          typeof sizeProp?.getValue === "function"
            ? Number(sizeProp.getValue(Cesium.JulianDate.now()) ?? 10)
            : Number(sizeProp) || 10;
        entity.point.pixelSize = new Cesium.ConstantProperty(
          Math.max(backup.pointSize + 4, 14),
        );
      }
      riskVisualBackup.set(key, backup);
    }
  } catch {
    // Viewer may not be ready.
  }
}

async function flyToLonLat(longitude: number, latitude: number, range = 12000) {
  camera?.flyToLonLat(longitude, latitude, range);
}

async function flyToPoints(
  points: Array<{ longitude?: number | null; latitude?: number | null }>,
  options?: { singleRange?: number },
) {
  camera?.flyToPoints(points, options);
}

function captureMapState() {
  savedCameraView = camera?.captureView() ?? null;
  savedScope = scope.value;
  savedLayerGroup = layerGroup.value;
  return {
    camera: savedCameraView,
    scope: savedScope,
    layerGroup: savedLayerGroup,
  };
}

function restoreMapState() {
  if (savedScope) scope.value = savedScope;
  if (savedLayerGroup) layerGroup.value = savedLayerGroup;
  if (savedCameraView) camera?.restoreView(savedCameraView);
  else resetView();
  clearE01Markers();
}

function clearE01Markers() {
  if (e01DataSource) {
    e01DataSource.entities.removeAll();
  }
}

/** E01 环境监测点 overlay 显隐（与 MapChrome「环境监测点」开关绑定） */
function applyE01MonitorVisibility() {
  if (e01DataSource) {
    e01DataSource.show = showMonitors.value;
  }
}

function syncE01Markers(markers: E01MapMarker[], selectedPointId: number | null | undefined) {
  try {
    const viewer = manager.get();
    if (!e01DataSource) {
      e01DataSource = new Cesium.CustomDataSource("e01-exceed-markers");
      viewer.dataSources.add(e01DataSource);
    }
    e01DataSource.entities.removeAll();
    const accent = Cesium.Color.fromCssColorString(tokens.e01Exceed);
    const selectedAccent = Cesium.Color.fromCssColorString(tokens.e01Selected);
    for (const marker of markers) {
      if (marker.longitude == null || marker.latitude == null) continue;
      const [lon, lat] = CoordinateAdapter.displayLngLat(marker.longitude, marker.latitude);
      const selected =
        selectedPointId != null
          ? marker.pointId === selectedPointId
          : Boolean(marker.highlighted);
      const dimmed =
        marker.dimmed === true ||
        (selectedPointId != null && marker.pointId !== selectedPointId);
      const shortLabel = marker.shortLabel || "点";
      const feature: TrafficMapFeature = {
        id: `e01-point-${marker.pointId}`,
        layerId: "e01-exceed",
        objectType: "e01-exceed-point",
        name: marker.label,
        geometry: { type: "Point", coordinates: [marker.longitude, marker.latitude] },
        properties: {
          e01EventId: marker.eventId,
          pointId: marker.pointId,
          status: marker.status,
          gisFeatureId: marker.gisFeatureId,
        },
        status: "warning",
        statusLabel: marker.status,
      };
      e01DataSource.entities.add({
        id: `e01-point-${marker.pointId}`,
        position: Cesium.Cartesian3.fromDegrees(lon, lat, 40),
        point: {
          pixelSize: selected ? 18 : dimmed ? 8 : 12,
          color: dimmed ? accent.withAlpha(0.28) : selected ? selectedAccent : accent,
          outlineColor: selected
            ? Cesium.Color.WHITE
            : Cesium.Color.WHITE.withAlpha(dimmed ? 0.25 : 0.9),
          outlineWidth: selected ? 4 : 2,
          heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        ellipse: selected
          ? {
              semiMajorAxis: 120,
              semiMinorAxis: 120,
              material: selectedAccent.withAlpha(0.18),
              outline: true,
              outlineColor: selectedAccent.withAlpha(0.7),
              outlineWidth: 2,
              height: 35,
              heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND,
            }
          : undefined,
        label: {
          // 标签放点下方，避免与走廊中点「1/2/3标段」气泡重叠
          text: selected ? `${shortLabel} · ${marker.label}` : shortLabel,
          font: crispLabelFont(selected ? 12 : 11),
          scale: LABEL_ATLAS_SCALE,
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 4,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.TOP,
          pixelOffset: new Cesium.Cartesian2(0, wholePx(selected ? 16 : 12)),
          showBackground: true,
          backgroundColor: Cesium.Color.fromCssColorString("#1a1208").withAlpha(
            selected ? 0.78 : 0.62,
          ),
          backgroundPadding: new Cesium.Cartesian2(6, 3),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(2000, 1.0, 52000, 0.75),
          show: !dimmed || selected,
        },
        properties: {
          trafficFeature: feature,
        },
      });
    }
    applyE01MonitorVisibility();
  } catch {
    // Viewer may not be ready yet.
  }
}

async function refreshLayer() {
  await refreshData();
}

async function loadRelations() {
  if (!selected.value) return;
  const currentAdapter = adapter.value;
  if (!("getRelations" in currentAdapter)) return;
  relationsLoading.value = true;
  try {
    const res = await currentAdapter.getRelations(selected.value, context());
    relationsData.value = res.items || [];
    if (res.summary && selected.value) {
      selected.value = { ...selected.value, relationSummary: res.summary };
    }
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "关联事项加载失败",
      recoverable: true,
    });
  } finally {
    relationsLoading.value = false;
  }
}

async function loadBusinessLinks() {
  if (!selected.value) return;
  const currentAdapter = adapter.value;
  if (!("getBusinessLinks" in currentAdapter)) return;
  businessLinksLoading.value = true;
  businessLinksOpen.value = true;
  businessLinksData.value = null;
  try {
    const res = await currentAdapter.getBusinessLinks(
      selected.value,
      context(),
    );
    businessLinksData.value = res;
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "关联业务加载失败",
      recoverable: true,
    });
  } finally {
    businessLinksLoading.value = false;
  }
}

function resetView() {
  if (props.dataMode === "shp" || props.dataMode === "api") {
    camera?.flyToRectangle(trafficGisConfig.projectRectangle);
  } else {
    camera?.reset(props.initialView);
  }
}

function northUp() {
  const viewer = manager.get();
  viewer.camera.cancelFlight();
  viewer.camera.setView({
    orientation: {
      heading: 0,
      pitch: viewer.camera.pitch,
      roll: 0,
    },
  });
  compassHeading.value = 0;
}

defineExpose({
  flyToFeature,
  flyToSection,
  flyToLonLat,
  flyToPoints,
  refreshLayer,
  resetView,
  captureMapState,
  restoreMapState,
  syncE01Markers,
  clearE01Markers,
  getFeatureScreenPoint,
  applyE02SelectionVisual,
  restoreE02SelectionVisual,
});

onMounted(async () => {
  await nextTick();
  const viewer = manager.create(canvas.value!);
  basemaps = new BasemapManager(viewer);
  spatialAssets = new SpatialAssetManager(viewer);
  basemaps.switchTo(activeBasemap.value);
  vectorLayers.value = vectorStore.load();
  assets.value = assetStore.load();
  camera = new CameraManager(viewer);
  if (trafficGisConfig.corridorLock.enabled) {
    camera.enableCorridorLock({
      rectangle: trafficGisConfig.corridorLock.rectangle,
      minHeight: trafficGisConfig.corridorLock.minHeight,
      maxHeight: trafficGisConfig.corridorLock.maxHeight,
    });
  }
  const updateHeading = () => {
    compassHeading.value = -Cesium.Math.toDegrees(viewer.camera.heading);
    emit("cameraMove");
  };
  updateHeading();
  removeCameraChanged = viewer.camera.changed.addEventListener(updateHeading);
  camera.reset(props.initialView);
  if (props.interactionEnabled) {
    picker = new PickManager(viewer);
    picker.bind(
      (f, e) => {
        highlighter.select(e);
        selected.value = f;
        relationsData.value = [];
        businessLinksData.value = null;
        businessLinksOpen.value = false;
        emit("featureClick", f);
        if (f.objectType === "e01-exceed-point") {
          const eventId = Number(f.properties?.e01EventId);
          const pointId = Number(f.properties?.pointId);
          if (Number.isFinite(pointId)) emit("e01PointSelect", pointId);
          if (Number.isFinite(eventId)) emit("e01EventSelect", eventId);
          return;
        }
        if (props.e03Active) {
          emit("e03FeatureSelect", f.id);
          void flyToFeature(f.id);
          return;
        }
        if (props.s02Active) {
          emit("s02FeatureSelect", f.id);
          void flyToFeature(f.id);
          return;
        }
        if (props.e02Active) {
          emit("e02FeatureSelect", f.id);
          void flyToFeature(f.id);
          return;
        }
        if (f.objectType === "road-section") void flyToFeature(f.id);
      },
      (f) => emit("featureHover", f || null),
      () => {
        if (props.e03Active) {
          highlighter.restore();
          selected.value = null;
          emit("e03MapBlankClick");
          return;
        }
        if (props.s02Active) {
          highlighter.restore();
          selected.value = null;
          emit("s02MapBlankClick");
          return;
        }
        if (props.e02Active) {
          highlighter.restore();
          selected.value = null;
          emit("e02MapBlankClick");
        }
      },
    );
  }
  resizeObserver = new ResizeObserver(() => manager.resize());
  resizeObserver.observe(root.value!);
  await syncAssets();
  await loadDefinitions();
  await load();
  if (
    (props.dataMode === "shp" || props.dataMode === "api") &&
    !props.sectionId
  ) {
    camera.flyToRectangle(trafficGisConfig.projectRectangle);
  }
  emit("ready", { viewerReady: true });
});

onBeforeUnmount(() => {
  loadVersion++;
  resizeObserver?.disconnect();
  removeCameraChanged?.();
  camera?.disableCorridorLock();
  picker?.destroy();
  highlighter.restore();
  spatialAssets?.destroy();
  registry.clear(manager.get());
  manager.destroy();
});

watch(
  () => props.sectionId,
  async (sectionId) => {
    availableLayers.value = [];
    await refreshData();
    if (sectionId) await flyToSection(sectionId);
    else resetView();
  },
);

watch(
  () => [props.currentTime, props.dataMode],
  async () => {
    availableLayers.value = [];
    await refreshData();
  },
  { deep: true },
);

watch(
  () => props.visibleLayerIds,
  (ids) => {
    if (ids) {
      visibleIds.value = [...ids];
      load();
    }
  },
  { deep: true },
);

watch(
  () => props.selectedFeatureId,
  (id) => {
    if (id) flyToFeature(id);
  },
);

watch(
  () => props.e02SelectedFeatureId,
  (id) => {
    if (!props.e02Active || !id) {
      if (!props.e02Active) restoreE02SelectionVisual();
      return;
    }
    const entity = findEntity(id);
    if (entity) highlighter.select(entity);
    // 飞近由 GisOverviewCesiumPanel.focusE02Issue 统一控制，避免双重 fly
  },
);

watch(
  () => props.e02Active,
  (active) => {
    if (!active) restoreE02SelectionVisual();
  },
);

watch(
  () => props.e03SelectedFeatureId,
  (id) => {
    if (!props.e03Active || !id) {
      if (!props.e03Active) restoreE02SelectionVisual();
      return;
    }
    const entity = findEntity(id);
    if (entity) highlighter.select(entity);
  },
);

watch(
  () => props.e03Active,
  (active) => {
    if (!active) restoreE02SelectionVisual();
  },
);

watch(
  () => props.s02SelectedFeatureId,
  (id) => {
    if (!props.s02Active || !id) {
      if (!props.s02Active) restoreE02SelectionVisual();
      return;
    }
    const entity = findEntity(id);
    if (entity) highlighter.select(entity);
  },
);

watch(
  () => props.s02Active,
  async (active) => {
    if (active) {
      if (!showRiskPoints.value) {
        showRiskPoints.value = true;
      } else {
        applyRiskEmphasis(true);
      }
    } else {
      restoreE02SelectionVisual();
    }
  },
);

watch(
  () => [props.e01Active, props.e01Markers, props.e01SelectedPointId] as const,
  ([active, markers, selectedId]) => {
    if (!active) {
      clearE01Markers();
      return;
    }
    syncE01Markers(markers || [], selectedId ?? null);
  },
  { deep: true },
);

watch(layerGroup, load);
watch(showRiskPoints, load);
watch(showMonitors, applyE01MonitorVisibility);
watch(scope, async () => {
    if (scope.value !== "all") {
      await flyToSection(scope.value);
    } else {
      resetView();
    }
  });

function handleOpenKpiSource(payload: GisBusinessLinkOpenPayload) {
  emit('openKpiSource', {
    ...payload,
    gisFeatureId: payload.gisFeatureId || selected.value?.id,
  });
}
</script>

<template>
  <div ref="root" class="traffic-gis-overview">
    <div ref="canvas" class="traffic-gis-overview__canvas"></div>
    <MapChrome
      :config-open="panelOpen"
      :heading="compassHeading"
      :show-config-button="showConfigButton"
      :presentation-mode="presentationMode"
      :section-scope="scope"
      :show-monitors="showMonitors"
      :show-risk-points="showRiskPoints"
      @north="northUp"
      @config="panelOpen = !panelOpen"
      @section-change="scope = $event"
      @toggle-monitors="showMonitors = !showMonitors"
      @toggle-risk-points="showRiskPoints = !showRiskPoints"
    />
    <div class="traffic-gis-overview__top">
      <div>
        <b>GIS 地图主视角</b>
        <span>空间态势 · 交通 · ESG</span>
      </div>
      <TrafficLegend v-if="showLegend" :highlight-key="e02LegendHighlightKey" />
    </div>
    <nav v-if="showModeSwitch" class="traffic-gis-overview__nav">
      <div class="nav-group">
        <span class="nav-label">范围</span>
        <button :class="{ active: scope === 'all' }" @click="scope = 'all'">全线</button>
        <button :class="{ active: scope === 'section-1' }" @click="scope = 'section-1'">标段一</button>
        <button :class="{ active: scope === 'section-2' }" @click="scope = 'section-2'">标段二</button>
        <button :class="{ active: scope === 'section-3' }" @click="scope = 'section-3'">标段三</button>
      </div>
      <div class="nav-group">
        <span class="nav-label">图层</span>
        <button :class="{ active: layerGroup === 'all' }" @click="layerGroup = 'all'">项目基础</button>
        <button :class="{ active: layerGroup === 'environment' }" @click="layerGroup = 'environment'">E环境</button>
        <button :class="{ active: layerGroup === 'social' }" @click="layerGroup = 'social'">S社会</button>
        <button :class="{ active: layerGroup === 'governance' }" @click="layerGroup = 'governance'">G治理</button>
        <button :class="{ active: layerGroup === 'situation' }" @click="layerGroup = 'situation'">综合态势</button>
      </div>
      <div class="nav-actions">
        <button @click="resetView">复位</button>
        <button
          v-if="showConfigButton"
          class="layer-button"
          :class="{ active: panelOpen }"
          @click="panelOpen = !panelOpen"
        >
          配置后台
        </button>
      </div>
    </nav>
    <LayerControl
      :open="panelOpen"
      :active-basemap="activeBasemap"
      :layers="availableLayers"
      :visible-ids="visibleIds"
      :vector-layers="vectorLayers"
      :assets="assets"
      :loading="loading"
      @close="panelOpen = false"
      @basemap-change="switchBasemap"
      @layer-toggle="toggleLayer"
      @layer-style="styleLayer"
      @vector-upload="addVector"
      @vector-toggle="toggleVector"
      @vector-style="styleVector"
      @vector-remove="removeVector"
      @vector-locate="locateVector"
      @asset-add="addAsset"
      @asset-toggle="toggleAsset"
      @asset-remove="removeAsset"
      @asset-locate="locateAsset"
      @refresh="refreshData"
    />
    <FeatureCard
      v-if="selected"
      class="traffic-gis-overview__detail"
      :feature="selected"
      :presentation-mode="presentationMode"
      :relations="relationsData"
      :relations-loading="relationsLoading"
      @close="selected = null"
      @load-relations="loadRelations"
      @load-business-links="loadBusinessLinks"
    />
    <BusinessLinksPanel
      v-if="selected && businessLinksOpen"
      class="traffic-gis-overview__business-links"
      :data="businessLinksData"
      :loading="businessLinksLoading"
      :feature-name="selected.name"
      :presentation-mode="presentationMode"
      @close="businessLinksOpen = false"
      @open-kpi-source="handleOpenKpiSource"
    />
    <div v-if="loading" class="traffic-gis-overview__loading">
      业务图层加载中…
    </div>
    <div class="traffic-gis-overview__mock">
      {{
        dataMode === "mock"
          ? "测试数据库数据"
          : dataMode === "shp"
            ? "SHP 实测空间数据"
            : "实时数据库数据"
      }}
    </div>
    <div v-if="isDemoData" class="traffic-gis-overview__demo-notice">
      当前展示测试空间数据
    </div>
  </div>
</template>

<style scoped>
.traffic-gis-overview {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 280px;
  overflow: hidden;
  background: #eef3f7;
  color: #d9f1ff;
}
.traffic-gis-overview__canvas {
  position: absolute;
  inset: 0;
}
.traffic-gis-overview__top {
  position: absolute;
  left: 14px;
  top: 12px;
  right: 14px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  pointer-events: none;
}
.traffic-gis-overview > .traffic-gis-overview__top,
.traffic-gis-overview > nav {
  display: none !important;
}
.traffic-gis-overview__top > div:first-child {
  padding: 8px 12px;
  background: rgba(4, 24, 48, 0.82);
  border-left: 3px solid #22d7ff;
}
.traffic-gis-overview__top b,
.traffic-gis-overview__top span {
  display: block;
}
.traffic-gis-overview__top b {
  font-size: 14px;
}
.traffic-gis-overview__top span {
  font-size: 10px;
  color: #6f93ac;
  margin-top: 3px;
}
.traffic-gis-overview__top :deep(.legend) {
  pointer-events: auto;
}
.traffic-gis-overview__nav {
  position: absolute;
  top: 67px;
  left: 14px;
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 9;
}
.nav-group {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: rgba(4, 24, 48, 0.85);
  border-radius: 4px;
}
.nav-label {
  font-size: 10px;
  color: #6f93ac;
  padding-right: 4px;
  border-right: 1px solid rgba(34, 135, 255, 0.3);
}
.nav-group button {
  padding: 5px 10px;
  color: #8eb6cb;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
}
.nav-group button.active {
  color: #d9f1ff;
  border-color: #22d7ff;
  background: rgba(20, 100, 145, 0.5);
}
.nav-actions {
  display: flex;
  gap: 6px;
}
.nav-actions button {
  padding: 5px 10px;
  color: #8eb6cb;
  background: rgba(4, 24, 48, 0.85);
  border: 1px solid rgba(34, 135, 255, 0.34);
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}
.nav-actions button.active {
  color: #d9f1ff;
  border-color: #22d7ff;
  background: rgba(20, 100, 145, 0.75);
}
.nav-actions .layer-button {
  margin-left: 0;
}
.traffic-gis-overview__detail {
  position: absolute;
  right: 18px;
  bottom: 14px;
  z-index: 10;
  max-width: calc(100% - 36px);
  max-height: calc(100% - 120px);
  overflow: hidden;
}
/* 关联业务侧浮层：限制在 GIS 面板内部右下角，不遮挡右侧专题和底部时间轴 */
.traffic-gis-overview__business-links {
  position: absolute;
  right: 18px;
  bottom: 14px;
  z-index: 11;
  max-width: calc(100% - 36px);
  max-height: calc(100% - 120px);
}
.traffic-gis-overview__loading {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  padding: 10px 16px;
  background: rgba(2, 11, 24, 0.78);
  font-size: 12px;
  pointer-events: none;
}
.traffic-gis-overview__mock {
  position: absolute;
  left: 14px;
  bottom: 10px;
  color: #6f93ac;
  font-size: 10px;
}
.traffic-gis-overview__demo-notice {
  position: absolute;
  right: 14px;
  bottom: 10px;
  padding: 4px 10px;
  background: rgba(255, 179, 71, 0.18);
  border: 1px solid rgba(255, 179, 71, 0.35);
  border-radius: 3px;
  color: #ffb347;
  font-size: 11px;
}
.traffic-gis-overview :deep(.cesium-viewer-toolbar) {
  display: none !important;
}
@media (max-width: 800px) {
  .traffic-gis-overview__top :deep(.legend) {
    display: none;
  }
  .traffic-gis-overview__detail {
    right: 14px;
  }
  .traffic-gis-overview__business-links {
    right: 14px;
  }
  .traffic-gis-overview nav {
    top: 58px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .traffic-gis-overview * {
    animation: none !important;
    transition: none !important;
  }
}
</style>
