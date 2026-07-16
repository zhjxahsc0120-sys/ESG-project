import * as Cesium from "cesium";
import { statusColors } from "../../config/style-tokens";
import type { TrafficMapFeature } from "../../types";
export const featureColor = (f: TrafficMapFeature, fallback: string) =>
  Cesium.Color.fromCssColorString(f.status ? statusColors[f.status] : fallback);
export const entityMeta = (f: TrafficMapFeature) => ({
  id: f.id,
  name: f.name,
  properties: { trafficFeature: f },
});
const iconGlyph:Record<string,string>={"slope-monitor":"!","spoil-site":"弃","water-source":"水","ecological-zone":"叶",risk:"!",monitor:"测"};
export function featureIcon(f:TrafficMapFeature,color:string){const glyph=iconGlyph[f.objectType]||'●';const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="44" height="54" viewBox="0 0 44 54"><filter id="g"><feGaussianBlur stdDeviation="2"/></filter><path d="M22 51S4 33 4 21a18 18 0 1 1 36 0c0 12-18 30-18 30z" fill="${color}" opacity=".45" filter="url(#g)"/><path d="M22 48S7 32 7 21a15 15 0 1 1 30 0c0 11-15 27-15 27z" fill="#06182a" stroke="${color}" stroke-width="2"/><circle cx="22" cy="21" r="10" fill="${color}" opacity=".22"/><text x="22" y="26" text-anchor="middle" font-family="Microsoft YaHei" font-size="13" font-weight="700" fill="white">${glyph}</text></svg>`;return`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`}
const xml=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]||char));
export function featureLabel(text:string,accent:string,textColor='#ffffff',fontSize=13){const width=Math.max(74,Array.from(text).length*fontSize+28);const height=42;const safe=xml(text);const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><defs><filter id="s"><feGaussianBlur stdDeviation="2"/></filter><linearGradient id="b" x2="1"><stop stop-color="#071b2d" stop-opacity=".96"/><stop offset="1" stop-color="#0b2c43" stop-opacity=".92"/></linearGradient></defs><rect x="3" y="3" width="${width-6}" height="28" rx="3" fill="${accent}" opacity=".35" filter="url(#s)"/><path d="M4 2H${width-4}V30H${width/2+6}L${width/2} 38L${width/2-6} 30H4Z" fill="url(#b)" stroke="${accent}" stroke-width="1.4"/><path d="M4 2H24" stroke="#fff" stroke-opacity=".75" stroke-width="2"/><text x="${width/2}" y="21" text-anchor="middle" font-family="Microsoft YaHei" font-size="${fontSize}" font-weight="600" fill="${textColor}">${safe}</text></svg>`;return{image:`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,width,height}}
