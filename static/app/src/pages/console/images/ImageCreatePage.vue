<script setup lang="ts">
import { ElAlert, ElRow, ElText } from 'element-plus'
import { useRouter } from 'vue-router'
import backIcon from '@/assets/svgs/icon-back-rounded.svg'
import ImageForm from './components/ImageForm.vue'
import { imageLabels } from './imageLabels'

const router = useRouter()
</script>

<template>
  <section class="image-create-page">
    <div class="image-create-head" @click="router.back()">
      <img class="back-icon" :src="backIcon" alt="" />
      <span>{{ imageLabels.createTitle }}</span>
    </div>

    <div class="image-create-card">
      <ElRow class="mb-3">
        <ElAlert type="warning" :closable="false">
          <template #title>
            <ElText type="info">
              {{ imageLabels.importTip }}
            </ElText>
          </template>
        </ElAlert>
      </ElRow>

      <ImageForm />
    </div>
  </section>
</template>

<style scoped>
.image-create-page {
  max-width: 1400px;
  margin: 0 auto 30px;
}

.image-create-head {
  display: flex;
  align-items: center;
  width: 100%;
  margin-bottom: 30px;
  cursor: pointer;
}

.image-create-head span {
  color: #292962;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0;
}

.back-icon {
  width: 32px;
  height: 32px;
  margin-right: 12px;
}

.image-create-card {
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: #fff;
  padding: 24px 100px;
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
}

@media (max-width: 1023px) {
  .image-create-card {
    padding: 20px;
  }
}
</style>
