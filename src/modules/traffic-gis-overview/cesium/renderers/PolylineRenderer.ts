import * as Cesium from "cesium";
import type { TrafficLayerDefinition, TrafficMapFeature } from "../../types";
import { CoordinateAdapter } from "../core/CoordinateAdapter";
import { entityMeta, featureColor,featureLabel } from "./render-utils";
export class PolylineRenderer {
  render(
    viewer: Cesium.Viewer,
    layer: TrafficLayerDefinition,
    features: TrafficMapFeature[],
  ) {
    return features.flatMap((f) => {
      if (f.geometry.type !== "LineString")
        throw new Error("PolylineRenderer收到非线要素");
      const positions = CoordinateAdapter.degreesArray(f.geometry.coordinates);
      const color = featureColor(f, layer.style.color);
      const midpoint =
        f.geometry.coordinates[Math.floor(f.geometry.coordinates.length / 2)];
      const tag=featureLabel(f.name,color.toCssColorString(),layer.style.labelColor||'#ffffff',layer.style.labelSize||13);const billboard=layer.style.showLabel===false?undefined:{image:tag.image,width:tag.width,height:tag.height,verticalOrigin:Cesium.VerticalOrigin.BOTTOM,pixelOffset:new Cesium.Cartesian2(0,-8),disableDepthTestDistance:Number.POSITIVE_INFINITY};
      return [
        viewer.entities.add({
          ...entityMeta(f),
          id: `${f.id}-glow`,
          polyline: {
            positions,
            width: (layer.style.width || 5) + 12,
            material: new Cesium.PolylineGlowMaterialProperty({
              color: color.withAlpha(0.72),glowPower: 0.38,
            }),
            clampToGround: false,
          },
        }),
        viewer.entities.add({
          ...entityMeta(f),
          position: CoordinateAdapter.wgs84(midpoint),
          billboard,
          polyline: {
            positions,
            width: layer.style.width || 5,
            material: color.withAlpha(layer.style.opacity ?? 1),
            clampToGround: false,
          },
        }),
      ];
    });
  }
}
