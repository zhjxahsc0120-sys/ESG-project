<script setup lang="ts">
defineProps<{
  title?: string
  icon?: object | (() => void)
}>()
</script>

<template>
  <div class="panel-card">
    <div v-if="title" class="panel-title">
      <component :is="icon" v-if="icon" class="panel-icon" />
      <span>{{ title }}</span>
    </div>
    <slot />
  </div>
</template>
