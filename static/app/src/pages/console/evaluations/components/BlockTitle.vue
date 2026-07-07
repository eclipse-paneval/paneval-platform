<script setup lang="ts"></script>

<template>
  <div class="block-title">
    <div class="round-bg"></div>
    <div class="underline-bg"></div>
    <div class="eval-title-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.block-title {
  position: relative;
  width: fit-content;
  padding-left: 12px;
  color: #333;
  font-size: 14px;
  font-weight: 700;
  line-height: 20px;
}

.round-bg {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 12px;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(
    135deg,
    rgb(23 98 238 / 40%) 0%,
    rgb(23 98 238 / 20%) 35%,
    rgb(23 98 238 / 0%) 100%
  );
}

.underline-bg {
  position: absolute;
  bottom: 0;
  left: 8px;
  width: 100%;
  height: 6px;
  border-radius: 8px;
  background: linear-gradient(90deg, rgb(23 98 238 / 50%) 0%, rgb(23 98 238 / 0%) 100%);
}

.eval-title-content {
  position: relative;
}
</style>
