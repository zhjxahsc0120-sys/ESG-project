<template>
  <div class="legend">
    <span :class="{ active: highlightKey === 's1' }"><i class="s1"></i>1标段</span>
    <span :class="{ active: highlightKey === 's2' }"><i class="s2"></i>2标段</span>
    <span :class="{ active: highlightKey === 's3' }"><i class="s3"></i>3标段</span>
    <span :class="{ active: highlightKey === 'water' }"><i class="water"></i>水源</span>
    <span :class="{ active: highlightKey === 'eco' }"><i class="eco"></i>生态</span>
    <span :class="{ active: highlightKey === 'spoil' }"><i class="spoil"></i>弃渣</span>
    <span :class="{ active: highlightKey === 'slope' }"><i class="slope"></i>边坡</span>
    <span :class="{ active: highlightKey === 'exceed' }"><i class="exceed"></i>超标点</span>
  </div>
</template>
<script setup lang="ts">
withDefaults(
  defineProps<{
    /** 当前选中对象对应的图例键：s1/s2/s3/water/eco/spoil/slope/exceed */
    highlightKey?: string | null;
  }>(),
  { highlightKey: null },
);
</script>
<style scoped>
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  max-width: 420px;
  padding: 7px 11px;
  background: rgba(4, 24, 48, 0.82);
  border: 1px solid rgba(77, 163, 255, 0.35);
  font-size: 11px;
  color: #a9c9da;
}
.legend span {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 1px 4px;
  border-radius: 3px;
  transition: color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.legend span.active {
  color: #eef8ff;
  background: rgba(105, 227, 111, 0.16);
  box-shadow: inset 0 0 0 1px rgba(105, 227, 111, 0.55);
}
.legend i {
  width: 10px;
  height: 3px;
  border-radius: 2px;
}
.legend i.water,
.legend i.eco,
.legend i.spoil {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  opacity: 0.9;
}
.legend i.slope,
.legend i.exceed {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.legend i.slope {
  border-radius: 1px;
  transform: rotate(45deg);
}
.s1 { background: #4da3ff; }
.s2 { background: #2ec8a6; }
.s3 { background: #f0b429; }
.water { background: #28a9e0; }
.eco { background: #35a853; }
.spoil { background: #c77d2d; }
.slope { background: #f05a47; }
.exceed { background: #ff9f2f; }
</style>
