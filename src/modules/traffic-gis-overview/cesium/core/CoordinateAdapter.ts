import * as Cesium from "cesium";
export class CoordinateAdapter {
  static wgs84(coordinates: number[]) {
    const [longitude, latitude, height = 0] = coordinates;
    if (Math.abs(longitude) > 180 || Math.abs(latitude) > 90)
      throw new Error("坐标不是有效WGS84经纬度");
    return Cesium.Cartesian3.fromDegrees(longitude, latitude, height);
  }
  static degreesArray(coordinates: number[][]) {
    return Cesium.Cartesian3.fromDegreesArrayHeights(
      coordinates.flatMap((c) => [c[0], c[1], c[2] || 0]),
    );
  }
}
