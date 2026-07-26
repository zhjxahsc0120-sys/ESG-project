export type SpatialAssetType = "imagery" | "terrain" | "tileset" | "pointcloud";
export interface SpatialAssetRecord {
  id: string;
  name: string;
  type: SpatialAssetType;
  url: string;
  visible: boolean;
  opacity: number;
  placement?: {
    longitude: number;
    latitude: number;
    height: number;
    labelHeight?: number;
  };
  label?: string;
  properties?: Record<string, unknown>;
}
const KEY = "traffic-esg-spatial-assets-v1";
export class SpatialAssetStore {
  load(): SpatialAssetRecord[] {
    try {
      const saved = JSON.parse(
        localStorage.getItem(KEY) || "[]",
      ) as SpatialAssetRecord[];
      return saved;
    } catch {
      return [];
    }
  }
  save(items: SpatialAssetRecord[]) {
    localStorage.setItem(KEY, JSON.stringify(items));
  }
  add(items: SpatialAssetRecord[], input: Omit<SpatialAssetRecord, "id">) {
    const next = [...items, { ...input, id: `asset-${Date.now()}` }];
    this.save(next);
    return next;
  }
  remove(items: SpatialAssetRecord[], id: string) {
    const next = items.filter((item) => item.id !== id);
    this.save(next);
    return next;
  }
}
