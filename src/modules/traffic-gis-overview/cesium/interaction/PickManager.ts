import * as Cesium from "cesium";
import type { TrafficMapFeature } from "../../types";
type PickResult = { feature: TrafficMapFeature; entity: Cesium.Entity };
export class PickManager {
  private handler?: Cesium.ScreenSpaceEventHandler;
  constructor(private readonly viewer: Cesium.Viewer) {}
  bind(
    onClick: (f: TrafficMapFeature, e: Cesium.Entity) => void,
    onHover: (f: TrafficMapFeature | null) => void,
  ) {
    this.handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
    this.handler.setInputAction(
      (e: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
        const result = this.pick(e.position);
        if (result) onClick(result.feature, result.entity);
      },
      Cesium.ScreenSpaceEventType.LEFT_CLICK,
    );
    this.handler.setInputAction(
      (e: Cesium.ScreenSpaceEventHandler.MotionEvent) =>
        onHover(this.pick(e.endPosition)?.feature ?? null),
      Cesium.ScreenSpaceEventType.MOUSE_MOVE,
    );
  }
  private pick(position: Cesium.Cartesian2): PickResult | undefined {
    const picked = this.viewer.scene.pick(position);
    const entity = picked?.id as Cesium.Entity | undefined;
    const feature = entity?.properties?.trafficFeature?.getValue(
      Cesium.JulianDate.now(),
    ) as TrafficMapFeature | undefined;
    return entity && feature ? { feature, entity } : undefined;
  }
  destroy() {
    this.handler?.destroy();
    this.handler = undefined;
  }
}
