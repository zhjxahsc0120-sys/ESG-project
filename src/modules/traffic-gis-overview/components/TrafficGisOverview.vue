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
} from "../types";
import { trafficGisConfig } from "../config/traffic-gis.config";

const props = withDefaults(defineProps<TrafficGisOverviewProps>(), {
  showLegend: true,
  showModeSwitch: true,
  showConfigButton: true,
  interactionEnabled: true,
  dataMode: "mock",
  presentationMode: "preview" as PresentationMode,
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
const mode = ref<"all" | "risk" | "construction" | "environment">("all");
const panelOpen = ref(false);
const activeBasemap = ref<BasemapId>(defaultBasemapId);
const availableLayers = ref<TrafficLayerDefinition[]>([]);
const visibleIds = ref<string[]>([]);
const vectorLayers = ref<VectorLayerRecord[]>([]);
const assets = ref<SpatialAssetRecord[]>([]);

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

const STYLE_STORAGE_KEY = "traffic-esg-business-layer-styles-v1";

function savedStyles() {
  try {
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

function modeAllows(layer: TrafficLayerDefinition) {
  if (mode.value === "all") return true;

  const type = layer.objectType || "";

  if (mode.value === "construction") {
    return ["road-section", "spoil-site", "chainage"].includes(type);
  }

  if (mode.value === "environment") {
    return ["water-source", "ecological-zone", "spoil-site"].includes(type);
  }

  if (mode.value === "risk") {
    return ["slope-monitor", "risk-point"].includes(type);
  }

  return true;
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
  const overrides = savedStyles();
  availableLayers.value = layers.map((layer) => ({
    ...layer,
    style: { ...layer.style, ...overrides[layer.id] },
  }));
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
    layers = layers.filter(modeAllows);
    let count = 0,
      warning = 0,
      offline = 0;
    for (const layer of layers) {
      try {
        const features = await adapter.value.getFeatures(layer, context());
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

async function flyToFeature(id: string) {
  const e = findEntity(id);
  if (e) await camera?.flyTo([e]);
}

async function flyToSection(sectionId: string) {
  const entities = registry
    .all()
    .filter((e) => featureOf(e)?.properties.sectionId === sectionId);
  if (entities.length) await camera?.flyTo(entities);
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

defineExpose({ flyToFeature, flyToSection, refreshLayer, resetView });

onMounted(async () => {
  await nextTick();
  const viewer = manager.create(canvas.value!);
  basemaps = new BasemapManager(viewer);
  spatialAssets = new SpatialAssetManager(viewer);
  basemaps.switchTo(activeBasemap.value);
  vectorLayers.value = vectorStore.load();
  assets.value = assetStore.load();
  camera = new CameraManager(viewer);
  const updateHeading = () =>
    compassHeading.value = -Cesium.Math.toDegrees(viewer.camera.heading);
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
        if (f.objectType === "road-section") void flyToFeature(f.id);
      },
      (f) => emit("featureHover", f || null),
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

watch(mode, load);

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
      :mode="mode"
      :config-open="panelOpen"
      :heading="compassHeading"
      :show-config-button="showConfigButton"
      :presentation-mode="presentationMode"
      @mode-change="mode = $event"
      @reset="resetView"
      @north="northUp"
      @config="panelOpen = !panelOpen"
    />
    <div class="traffic-gis-overview__top">
      <div>
        <b>GIS 地图主视角</b>
        <span>空间态势 · 交通 · ESG</span>
      </div>
      <TrafficLegend v-if="showLegend" />
    </div>
    <nav v-if="showModeSwitch">
      <button :class="{ active: mode === 'all' }" @click="mode = 'all'">
        全线
      </button>
      <button
        :class="{ active: mode === 'construction' }"
        @click="mode = 'construction'"
      >
        施工
      </button>
      <button :class="{ active: mode === 'risk' }" @click="mode = 'risk'">
        风险
      </button>
      <button @click="resetView">复位</button>
      <button
        v-if="showConfigButton"
        class="layer-button"
        :class="{ active: panelOpen }"
        @click="panelOpen = !panelOpen"
      >
        配置后台
      </button>
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
          ? "演示数据库数据"
          : dataMode === "shp"
            ? "SHP 实测空间数据"
            : "实时数据库数据"
      }}
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
.traffic-gis-overview nav {
  position: absolute;
  top: 67px;
  left: 14px;
  display: flex;
  gap: 5px;
  z-index: 9;
}
.traffic-gis-overview button {
  padding: 6px 12px;
  color: #8eb6cb;
  background: rgba(4, 24, 48, 0.9);
  border: 1px solid rgba(34, 135, 255, 0.34);
  cursor: pointer;
}
.traffic-gis-overview button.active {
  color: #d9f1ff;
  border-color: #22d7ff;
  background: rgba(20, 100, 145, 0.75);
}
.traffic-gis-overview .layer-button {
  margin-left: 5px;
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
.traffic-gis-overview :deep(.cesium-viewer-bottom),
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
