export const trafficGisConfig = {
  initialView: {
    longitude: 109.68,
    latitude: 24.45,
    height: 48000,
    heading: 0,
    pitch: -55,
  },
  /** 复位 / 总览飞入框（WGS84） */
  projectRectangle: [109.52, 24.39, 109.83, 24.52] as [
    number,
    number,
    number,
    number,
  ],
  /**
   * 相机硬边界：在 projectRectangle 外扩约 10%，
   * 限制拖出 / 过度缩小，锁定在 1–3 标段走廊。
   */
  corridorLock: {
    enabled: true,
    rectangle: [109.489, 24.377, 109.861, 24.533] as [
      number,
      number,
      number,
      number,
    ],
    minHeight: 3200,
    maxHeight: 58000,
  },
  basemap: {
    url:
      import.meta.env.VITE_TRAFFIC_BASEMAP_URL ||
      "https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
    brightness: 0.9,
    contrast: 1.08,
    saturation: 0.9,
  },
  lod: { labelMaxHeight: 55000, pointMaxHeight: 120000 },
};
