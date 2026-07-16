import * as Cesium from "cesium";
export class HighlightManager {
  private selected?: Cesium.Entity;
  select(entity?: Cesium.Entity) {
    this.restore();
    this.selected = entity;
    if (entity?.point) {
      entity.point.pixelSize = new Cesium.ConstantProperty(20);
      entity.point.outlineColor = new Cesium.ConstantProperty(
        Cesium.Color.CYAN,
      );
    }
  }
  restore() {
    if (this.selected?.point)
      this.selected.point.pixelSize = new Cesium.ConstantProperty(12);
    this.selected = undefined;
  }
}
