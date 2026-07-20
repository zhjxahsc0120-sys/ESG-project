<script setup lang="ts">
import type { PresentationMode } from '../types';

withDefaults(defineProps<{
  mode: 'all' | 'construction' | 'environment' | 'risk';
  configOpen: boolean;
  heading: number;
  showConfigButton?: boolean;
  presentationMode?: PresentationMode;
}>(), {
  showConfigButton: true,
  presentationMode: 'preview',
});

defineEmits<{
  modeChange: ['all' | 'construction' | 'environment' | 'risk'];
  reset: [];
  north: [];
  config: [];
}>();
</script>

<template>
  <div class="chrome" :class="{ 'chrome--dashboard': presentationMode === 'dashboard' }">
    <div class="frame">
      <i></i><i></i><i></i><i></i>
    </div>
    <div v-if="presentationMode !== 'dashboard'" class="title">
      <b>GIS 地图主视览</b>
      <span>空间态势 + 时序影像</span>
    </div>
    <div class="tools">
      <span>图层切换</span>
      <button :class="{ active: mode === 'all' }" @click="$emit('modeChange', 'all')">全线</button>
      <button :class="{ active: mode === 'construction' }" @click="$emit('modeChange', 'construction')">标段</button>
      <button :class="{ active: mode === 'environment' }" @click="$emit('modeChange', 'environment')">环保点位</button>
      <button :class="{ active: mode === 'risk' }" @click="$emit('modeChange', 'risk')">风险点</button>
      <button @click="$emit('reset')">复位</button>
      <button v-if="showConfigButton" :class="{ active: configOpen }" @click="$emit('config')">配置后台</button>
    </div>
    <button class="compass" title="点击回正北" @click="$emit('north')">
      <span class="rose" :style="{ transform: `rotate(${heading}deg)` }">
        <b>N</b><i>▲</i><i>◆</i><small>S</small>
      </span>
    </button>
  </div>
</template>

<style scoped>
.chrome,
.frame {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.chrome {
  z-index: 8;
}
.frame {
  border: 1px solid rgba(19, 201, 240, 0.5);
  box-shadow: inset 0 0 38px rgba(0, 126, 180, 0.12);
}
.frame i {
  position: absolute;
  width: 38px;
  height: 18px;
  border-color: #21d4f4;
}
.frame i:nth-child(1) { left: 0; top: 0; border-left: 3px solid; border-top: 3px solid; }
.frame i:nth-child(2) { right: 0; top: 0; border-right: 3px solid; border-top: 3px solid; }
.frame i:nth-child(3) { left: 0; bottom: 0; border-left: 3px solid; border-bottom: 3px solid; }
.frame i:nth-child(4) { right: 0; bottom: 0; border-right: 3px solid; border-bottom: 3px solid; }

.title {
  position: absolute;
  left: 16px;
  top: 13px;
  padding: 8px 16px;
  background: linear-gradient(90deg, rgba(3, 25, 43, 0.95), rgba(3, 25, 43, 0.35));
  border-left: 3px solid #20d4f2;
  pointer-events: auto;
}
.title b, .title span { display: block; }
.title b { color: #29d9f5; font-size: 16px; }
.title span { margin-top: 3px; color: #6ba5ba; font-size: 10px; }

.tools {
  position: absolute;
  left: 50%;
  top: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transform: translateX(-50%);
  padding: 6px;
  background: rgba(3, 20, 38, 0.9);
  border: 1px solid rgba(36, 139, 204, 0.35);
  pointer-events: auto;
}
.tools > span {
  padding: 0 8px;
  color: #7399ae;
  font-size: 10px;
}
.tools button {
  padding: 7px 13px;
  border: 1px solid rgba(42, 116, 172, 0.45);
  background: #061b31;
  color: #a7c8da;
  cursor: pointer;
}
.tools button:hover,
.tools button.active {
  border-color: #18cbf0;
  color: #fff;
  background: #0b4a70;
}

.compass {
  position: absolute;
  right: 19px;
  top: 67px;
  width: 62px;
  height: 62px;
  padding: 0;
  border: 1px solid rgba(34, 193, 224, 0.35);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(8, 48, 68, 0.9), rgba(2, 14, 27, 0.72));
  box-shadow: 0 0 18px rgba(19, 197, 235, 0.2);
  pointer-events: auto;
  cursor: pointer;
}
.rose {
  position: absolute;
  inset: 5px;
  display: block;
  border: 1px solid rgba(133, 221, 239, 0.3);
  border-radius: 50%;
  transition: transform 0.12s linear;
}
.rose b, .rose small, .rose i {
  position: absolute;
  color: #dff9ff;
  font-style: normal;
  text-shadow: 0 0 7px #18c7eb;
}
.rose b { left: 50%; top: 1px; transform: translateX(-50%); font-size: 10px; color: #ff6e6e; }
.rose small { left: 50%; bottom: 1px; transform: translateX(-50%); font-size: 8px; }
.rose i:nth-of-type(1) { left: 50%; top: 12px; transform: translateX(-50%); font-size: 19px; color: #ff7474; }
.rose i:nth-of-type(2) { left: 50%; top: 23px; transform: translateX(-50%) rotate(45deg); font-size: 14px; color: #a8efff; }

/* Dashboard 模式：更紧凑的工具条 */
.chrome--dashboard .tools {
  top: 10px;
  gap: 4px;
  padding: 4px;
}
.chrome--dashboard .tools > span {
  padding: 0 5px;
  font-size: 9px;
}
.chrome--dashboard .tools button {
  padding: 5px 9px;
  font-size: 11px;
}
.chrome--dashboard .compass {
  width: 50px;
  height: 50px;
  top: 56px;
  right: 14px;
}
.chrome--dashboard .title b {
  font-size: 14px;
}
.chrome--dashboard .title span {
  font-size: 9px;
}

@media (max-width: 1050px) {
  .tools { left: 16px; top: 70px; transform: none; }
  .compass { display: none; }
}
</style>
