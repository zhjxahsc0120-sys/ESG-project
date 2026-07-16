import * as Cesium from "cesium";
import { trafficGisConfig } from "../../config/traffic-gis.config";
export class ViewerManager {
  private viewer?: Cesium.Viewer;
  create(container: HTMLElement) {
    if (this.viewer) return this.viewer;
    const imagery = new Cesium.OpenStreetMapImageryProvider({
      url: trafficGisConfig.basemap.url,
    });
    this.viewer = new Cesium.Viewer(container, {
      baseLayer: new Cesium.ImageryLayer(imagery),
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      animation: false,
      timeline: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
    });
    const layer = this.viewer.imageryLayers.get(0);
    layer.brightness = trafficGisConfig.basemap.brightness;
    layer.contrast = trafficGisConfig.basemap.contrast;
    layer.saturation = trafficGisConfig.basemap.saturation;
    this.viewer.scene.backgroundColor =
      Cesium.Color.fromCssColorString("#eef3f7");
    this.viewer.scene.globe.baseColor =
      Cesium.Color.fromCssColorString("#dce6ec");
    this.viewer.scene.screenSpaceCameraController.inertiaSpin=0;
    return this.viewer;
  }
  get() {
    if (!this.viewer) throw new Error("Viewer尚未创建");
    return this.viewer;
  }
  resize() {
    this.viewer?.resize();
  }
  destroy() {
    if (this.viewer && !this.viewer.isDestroyed()) this.viewer.destroy();
    this.viewer = undefined;
  }
}
