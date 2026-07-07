<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import heroVideoUrl from '@/assets/home/video/paneval-home-bg.mp4'
import domainTextureUrl from '@/assets/home/paneval-bg.webp'
import progressTextureUrl from '@/assets/home/home-progress-bg.webp'
import scientificIconUrl from '@/assets/home/se-icon.webp'
import fairIconUrl from '@/assets/home/inj-icon.webp'
import authoritativeIconUrl from '@/assets/home/po-icon.webp'
import openIconUrl from '@/assets/home/op-icon.webp'
import flowFrameUrl from '@/assets/home/line-9.png'
import flowLineUrl from '@/assets/home/line10.png'
import flowLine2Url from '@/assets/home/line2.png'
import flowLine3Url from '@/assets/home/line3.png'
import flowLine3ArrowUrl from '@/assets/home/line3-arrow.png'
import flowLine4Url from '@/assets/home/line4.png'
import flowLine5Url from '@/assets/home/line5.png'
import corpusIconUrl from '@/assets/home/flow-group-1.svg'
import pretrainIconUrl from '@/assets/home/flow-group-2.svg'
import finetuneIconUrl from '@/assets/home/flow-group-3.svg'
import autoEvalIconUrl from '@/assets/home/flow-group-4.svg'
import leaderboardIconUrl from '@/assets/home/flow-group-9.svg'
import humanEvalIconUrl from '@/assets/home/flow-group-11.svg'
import applicationIconUrl from '@/assets/home/flow-group-12.svg'
import monitorIconUrl from '@/assets/home/flow-group-13.svg'
import checkIconUrl from '@/assets/home/flow-group-17.svg'
import inferenceIconUrl from '@/assets/home/process-icon.webp'

type Domain = {
  name: string
  title: string
  description: string
  capabilities: {
    title: string
    text: string
  }[]
}

const features = [
  {
    icon: scientificIconUrl,
    title: 'Scientific'
  },
  {
    icon: fairIconUrl,
    title: 'Fair'
  },
  {
    icon: authoritativeIconUrl,
    title: 'Authoritative'
  },
  {
    icon: openIconUrl,
    title: 'Open'
  }
] as const

const domains: Domain[] = [
  {
    name: 'LLM',
    title: 'LLM',
    description:
      'The evaluation focuses on assessing various capabilities of large language models. In addition to custom datasets, several underexplored public datasets were selected for mainstream capability categories.',
    capabilities: [
      {
        title: 'Basic Language Processing',
        text: "Evaluates the model's performance in information analysis, extraction, summarization, and cross-lingual understanding."
      },
      {
        title: 'Mathematical Ability',
        text: "Assesses the model's capacity to perform operations using mathematical theorems and abstract symbols."
      },
      {
        title: 'Coding Proficiency',
        text: "Measures the model's ability to write, understand, and optimize computer code."
      },
      {
        title: 'Knowledge Application',
        text: "Tests the model's capability to answer questions accurately using common sense and specialized knowledge."
      },
      {
        title: 'Reasoning Ability',
        text: "Evaluates the model's ability to make logical inferences based on known information, common sense, and reasoning rules."
      },
      {
        title: 'Task Solving',
        text: "Assesses the model's effectiveness in understanding requirements, utilizing resources, and completing specific tasks."
      },
      {
        title: 'Instruction Following',
        text: 'The ability of a model to respond to questions by adhering to specific user instructions.'
      },
      {
        title: 'Safety and Values',
        text: 'Ensures the model generates content that is safe, non-toxic, non-discriminatory, and aligned with core human values.'
      }
    ]
  },
  {
    name: 'VLM',
    title: 'VLM',
    description:
      "Assessing the model's multi-dimensional performance in tasks such as image-text classification, image-text matching, and image-text generation.",
    capabilities: [
      {
        title: 'Vision-Language Models',
        text: 'Evaluates cross-modal understanding using 9 objective benchmarks based on visual question answering.'
      },
      {
        title: 'Text-to-Image',
        text: 'Assesses image-text consistency and image quality with 1 subjective benchmark and 5 objective benchmarks.'
      },
      {
        title: 'Text-to-Video',
        text: 'Evaluates video generation consistency, realism, quality, and aesthetics with 2 subjective benchmarks.'
      }
    ]
  }
]

const flowSectionRef = ref<HTMLElement | null>(null)
const isFlowVisible = ref(false)
let flowObserver: IntersectionObserver | null = null

onMounted(() => {
  flowObserver = new IntersectionObserver(
    ([entry]) => {
      if (!entry?.isIntersecting) return
      isFlowVisible.value = true
      flowObserver?.disconnect()
      flowObserver = null
    },
    {
      threshold: 0.28
    }
  )

  if (flowSectionRef.value) {
    flowObserver.observe(flowSectionRef.value)
  }
})

onBeforeUnmount(() => {
  flowObserver?.disconnect()
})
</script>

<template>
  <div class="home-page">
    <section class="hero-section">
      <video class="hero-video" autoplay muted loop playsinline aria-hidden="true">
        <source :src="heroVideoUrl" type="video/mp4" />
      </video>
      <div class="hero-shade" />

      <div class="hero-content">
        <h1>Large Model Evaluation Platform</h1>
        <p class="hero-copy">
          Build scientific, fair, and open benchmarks, methods, and tools that help researchers
          understand the real capability boundaries of foundation models and training algorithms.
        </p>
        <div class="hero-actions" aria-label="Homepage actions">
          <RouterLink class="primary-action" to="/console">Open Console</RouterLink>
        </div>
      </div>
    </section>

    <section class="intro-section" aria-labelledby="home-intro-title">
      <div class="intro-content">
        <p id="home-intro-title" class="intro-description">
          The platform has already launched linguistic large model evaluation, multilingual
          text-to-graph evaluation and text-to-graph generation evaluation tools, covering a wide
          range of language base models and cross-modal models. The evaluation scenes cover Natural
          Language Processing (NLP), Computer Vision (CV), Audio Processing (Audio) and Multimodal,
          supporting diverse downstream tasks.
        </p>
      </div>

      <div class="feature-grid">
        <article v-for="feature in features" :key="feature.title" class="feature-card">
          <div class="feature-icon">
            <img :src="feature.icon" :alt="`${feature.title} icon`" />
          </div>
          <h3>{{ feature.title }}</h3>
        </article>
      </div>
    </section>

    <section
      class="domain-section"
      :style="{ backgroundImage: `url(${domainTextureUrl})` }"
      aria-labelledby="domain-title"
    >
      <div class="section-heading">
        <h2 id="domain-title">Evaluation Domains</h2>
        <p class="domain-subtitle">Diverse Evaluation Tasks</p>
      </div>

      <div class="domain-list">
        <section v-for="domain in domains" :key="domain.name" class="domain-item">
          <h3>{{ domain.title }}</h3>
          <p class="domain-description">{{ domain.description }}</p>

          <div class="domain-card-grid">
            <article
              v-for="capability in domain.capabilities"
              :key="`${domain.name}-${capability.title}`"
              class="domain-card"
            >
              <h4>{{ capability.title }}</h4>
              <p>{{ capability.text }}</p>
            </article>
          </div>
        </section>
      </div>
    </section>

    <section
      ref="flowSectionRef"
      class="flow-section"
      :class="{ 'is-flow-visible': isFlowVisible }"
      :style="{ backgroundImage: `url(${progressTextureUrl})` }"
      aria-labelledby="flow-title"
    >
      <div class="section-heading">
        <h2 id="flow-title">Evaluation Flow</h2>
      </div>

      <div class="flow-diagram" aria-label="Evaluation flow diagram">
        <img class="flow-arrow flow-line arrow-1 stage-2" :src="flowLineUrl" alt="" />
        <img class="flow-arrow flow-line arrow-2 stage-4" :src="flowLineUrl" alt="" />
        <img class="flow-arrow flow-line arrow-3 stage-6" :src="flowLineUrl" alt="" />
        <img class="flow-arrow flow-line arrow-4 stage-8" :src="flowLineUrl" alt="" />
        <img class="flow-arrow flow-line arrow-5 stage-11" :src="flowLineUrl" alt="" />
        <img class="flow-arrow flow-line arrow-6 stage-13" :src="flowLineUrl" alt="" />
        <img class="flow-branch flow-line branch-line arrow-7 stage-9" :src="flowLine2Url" alt="" />
        <span class="flow-branch flow-reveal arrow-8 stage-10">
          <img :src="flowLine3Url" alt="" />
          <img class="line-arrow" :src="flowLine3ArrowUrl" alt="" />
        </span>
        <img class="flow-branch flow-reveal arrow-9 stage-10" :src="flowLine4Url" alt="" />
        <img class="flow-branch flow-reveal arrow-10 stage-10" :src="flowLine5Url" alt="" />

        <div
          class="flow-frame flow-reveal dataset-frame stage-1"
          :style="{ backgroundImage: `url(${flowFrameUrl})` }"
        >
          <div class="flow-node inner-node top-node">
            <img :src="corpusIconUrl" alt="" />
            <p>Corpus</p>
            <span>Public Datasets</span>
          </div>
          <div class="flow-node inner-node bottom-node">
            <img :src="corpusIconUrl" alt="" />
            <p>Self-built datasets</p>
            <span>Self-built Datasets</span>
          </div>
        </div>

        <div class="flow-node flow-reveal single-node pretrain-node stage-3">
          <img :src="pretrainIconUrl" alt="" />
          <p>Pre-train Model</p>
          <span>Pre-trained Model</span>
        </div>

        <div class="flow-node flow-reveal single-node finetune-node stage-5">
          <img :src="finetuneIconUrl" alt="" />
          <p>Fine-tuned Model</p>
          <span>Fine-tuned Model</span>
        </div>

        <div class="flow-node flow-reveal single-node inference-node stage-7">
          <img :src="inferenceIconUrl" alt="" />
          <p>Inference Service</p>
          <span>Inference Service</span>
        </div>

        <div
          class="flow-frame flow-reveal evaluation-frame stage-9"
          :style="{ backgroundImage: `url(${flowFrameUrl})` }"
        >
          <div class="flow-node inner-node top-node">
            <img :src="autoEvalIconUrl" alt="" />
            <p>Auto Evaluation</p>
            <span>Auto Evaluation</span>
          </div>
          <div class="flow-node inner-node bottom-node">
            <img :src="humanEvalIconUrl" alt="" />
            <p>Human Evaluation</p>
            <span>Human Evaluation</span>
          </div>
        </div>

        <div class="flow-node flow-reveal single-node check-node stage-12">
          <img :src="checkIconUrl" alt="" />
          <p>Check</p>
          <span>Check</span>
        </div>

        <div class="flow-node flow-reveal single-node leaderboard-node stage-14">
          <img :src="leaderboardIconUrl" alt="" />
          <p>Leaderboard</p>
          <span>Leaderboard</span>
        </div>

        <div class="flow-node flow-reveal single-node monitor-node stage-11">
          <img :src="monitorIconUrl" alt="" />
          <p>Monitor</p>
          <span>Monitoring Notice</span>
        </div>

        <div class="flow-node flow-reveal single-node application-node stage-11">
          <img :src="applicationIconUrl" alt="" />
          <p>Other Application</p>
          <span>Other Applications</span>
        </div>
      </div>

      <div class="flow-mobile-list" aria-label="Evaluation flow steps">
        <article class="flow-card stage-1">
          <img :src="corpusIconUrl" alt="" />
          <p>Corpus</p>
          <h3>Public / Self-built Datasets</h3>
        </article>
        <article class="flow-card stage-2">
          <img :src="pretrainIconUrl" alt="" />
          <p>Pre-train Model</p>
          <h3>Pre-trained Model</h3>
        </article>
        <article class="flow-card stage-3">
          <img :src="finetuneIconUrl" alt="" />
          <p>Fine-tuned Model</p>
          <h3>Fine-tuned Model</h3>
        </article>
        <article class="flow-card stage-4">
          <img :src="inferenceIconUrl" alt="" />
          <p>Inference Service</p>
          <h3>Inference Service</h3>
        </article>
        <article class="flow-card stage-5">
          <img :src="autoEvalIconUrl" alt="" />
          <p>Auto Evaluation</p>
          <h3>Auto Evaluation</h3>
        </article>
        <article class="flow-card stage-6">
          <img :src="humanEvalIconUrl" alt="" />
          <p>Human Evaluation</p>
          <h3>Human Evaluation</h3>
        </article>
        <article class="flow-card stage-7">
          <img :src="checkIconUrl" alt="" />
          <p>Check</p>
          <h3>Check</h3>
        </article>
        <article class="flow-card stage-8">
          <img :src="leaderboardIconUrl" alt="" />
          <p>Leaderboard</p>
          <h3>Leaderboard</h3>
        </article>
        <article class="flow-card stage-9">
          <img :src="monitorIconUrl" alt="" />
          <p>Monitor</p>
          <h3>Monitoring Notice</h3>
        </article>
        <article class="flow-card stage-10">
          <img :src="applicationIconUrl" alt="" />
          <p>Other Application</p>
          <h3>Other Applications</h3>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  --home-title-color: #292962;
  --home-text-color: #61616e;
  --home-description-color: #6e74a1;
  --home-subdescription-color: #4a4e6d;
  --home-gradient: linear-gradient(92deg, #2a91ff 0%, #6832fd 100%);
  --home-button-gradient: linear-gradient(89deg, #6832fd 0%, #2a91ff 100%);

  overflow: hidden;
  background: #fbfcff;
  color: var(--home-title-color);
}

.hero-section {
  position: relative;
  min-height: min(860px, calc(100vh - 4rem));
  display: flex;
  align-items: center;
  isolation: isolate;
}

.hero-video,
.hero-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-video {
  object-fit: cover;
  z-index: -2;
}

.hero-shade {
  z-index: -1;
  background:
    linear-gradient(
      90deg,
      rgb(248 251 255 / 95%) 0%,
      rgb(248 251 255 / 82%) 42%,
      rgb(248 251 255 / 22%) 100%
    ),
    radial-gradient(circle at 16% 28%, rgb(21 184 166 / 18%), transparent 28%);
}

.hero-content {
  width: min(760px, calc(100% - 40px));
  margin-left: clamp(20px, 8vw, 132px);
  padding: 88px 0 116px;
}

.eyebrow {
  margin: 0 0 14px;
  color: #1762ee;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  max-width: 860px;
  margin-bottom: 28px;
  color: var(--home-title-color);
  font-size: clamp(3.25rem, 6.8vw, 5rem);
  font-weight: 850;
  line-height: 1;
  text-wrap: balance;
}

h2 {
  margin-bottom: 18px;
  color: var(--home-title-color);
  font-size: clamp(2.1rem, 5vw, 4rem);
  font-weight: 820;
  line-height: 1.08;
}

h3 {
  color: var(--home-title-color);
  font-size: 1.05rem;
  line-height: 1.35;
}

.hero-copy {
  max-width: 680px;
  color: var(--home-description-color);
  font-size: clamp(1.05rem, 2vw, 1.32rem);
  line-height: 1.58;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-actions {
  margin-top: 48px;
}

.primary-action,
.secondary-action {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  padding: 0 34px;
  font-size: 0.95rem;
  font-weight: 500;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.primary-action {
  min-width: 172px;
  color: #fff;
  background: var(--home-button-gradient);
  box-shadow: 0 2px 8px 0 #dee6ef;
}

.secondary-action {
  color: var(--home-title-color);
  background: #fff;
  box-shadow: 0 2px 8px 0 #dee6ef;
}

.primary-action:hover,
.secondary-action:hover {
  transform: translateY(-2px);
}

.intro-section,
.domain-section,
.flow-section {
  padding: clamp(72px, 9vw, 128px) clamp(20px, 5vw, 72px);
}

.intro-section {
  max-width: 1440px;
  margin: 0 auto;
  padding-top: 40px;
  padding-bottom: 300px;
}

.intro-content {
  max-width: 1368px;
  margin: 0 auto 100px;
}

.intro-description {
  margin-bottom: 0;
  color: var(--home-title-color);
  font-size: 1.5rem;
  line-height: 1.5;
}

.section-heading {
  max-width: 860px;
  margin: 0 auto 56px;
  text-align: center;
}

.section-heading p:not(.eyebrow) {
  color: var(--home-subdescription-color);
  font-size: 1rem;
  line-height: 1.8;
}

.feature-grid {
  width: min(1180px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 18px;
}

.feature-grid {
  max-width: 100%;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.domain-card {
  border: 1px solid rgb(23 98 238 / 10%);
  border-radius: 8px;
  background: rgb(255 255 255 / 86%);
  box-shadow: 0 18px 42px rgb(20 32 92 / 8%);
}

.feature-card {
  text-align: center;
}

.feature-icon {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-icon img {
  height: 100%;
  object-fit: contain;
}

.feature-card h3 {
  margin-top: 20px;
  margin-bottom: 0;
  color: var(--home-title-color);
  font-size: 28px;
  font-weight: 700;
  line-height: 32px;
}

.domain-section,
.flow-section {
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
}

.domain-section {
  background-position: right center;
}

.domain-subtitle {
  margin-bottom: 0;
  color: var(--home-title-color);
  font-size: clamp(1.75rem, 3vw, 2.25rem);
  font-weight: 400;
  line-height: 1.18;
}

.domain-list {
  width: min(1200px, 100%);
  margin: 0 auto;
}

.domain-item {
  margin-bottom: 120px;
}

.domain-item:last-child {
  margin-bottom: 0;
}

.domain-item > h3 {
  margin-bottom: 24px;
  color: #1762ee;
  font-size: 28px;
  font-weight: 700;
  line-height: 33px;
  text-align: center;
}

.domain-description {
  max-width: 980px;
  margin: 0 auto 84px;
  color: var(--home-subdescription-color);
  font-size: 16px;
  font-weight: 400;
  line-height: 24px;
  text-align: center;
}

.domain-card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.domain-card {
  min-height: 152px;
  padding: 40px;
}

.domain-card h4 {
  margin: 0 0 8px;
  color: var(--home-title-color);
  font-size: 16px;
  font-weight: 700;
  line-height: 24px;
}

.domain-card p {
  margin-bottom: 0;
  color: var(--home-text-color);
  font-size: 14px;
  font-weight: 400;
  line-height: 16px;
}

.flow-section {
  overflow-x: hidden;
  padding-bottom: clamp(40px, 5vw, 72px);
}

.flow-section .section-heading {
  opacity: 0;
  transform: translateY(18px);
  transition:
    opacity 500ms ease,
    transform 500ms ease;
}

.flow-section.is-flow-visible .section-heading {
  opacity: 1;
  transform: translateY(0);
}

.flow-diagram {
  position: relative;
  left: 50%;
  width: 1440px;
  height: 700px;
  margin: 0 0 calc(700px * (var(--flow-scale, 1) - 1));
  transform: translateX(-50%) scale(var(--flow-scale, 1));
  transform-origin: top center;
}

.flow-frame,
.flow-node,
.flow-arrow,
.flow-branch {
  position: absolute;
}

.flow-frame {
  width: 160px;
  height: 411px;
  background-repeat: no-repeat;
  background-size: 100% 100%;
}

.dataset-frame {
  top: 0;
  left: 0;
}

.evaluation-frame {
  top: 0;
  left: 772px;
}

.flow-node {
  text-align: center;
}

.flow-node img {
  width: 80px;
  margin: 0 auto;
}

.flow-node p {
  margin: 14px 0 0;
  color: #666;
  font-size: 12px;
  font-weight: 700;
  line-height: 16px;
}

.flow-node span {
  display: none;
  color: var(--home-title-color);
  font-size: 14px;
  line-height: 20px;
}

.flow-reveal {
  opacity: 0;
  transform: translateY(18px) scale(0.985);
  transition:
    opacity 300ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 300ms cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--flow-delay, 0ms);
}

.flow-section.is-flow-visible .flow-reveal {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.flow-line {
  opacity: 0;
  clip-path: inset(0 100% 0 0);
  transition:
    clip-path 300ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 160ms ease;
  transition-delay: var(--flow-delay, 0ms);
}

.branch-line {
  clip-path: inset(0 0 100% 0);
}

.flow-section.is-flow-visible .flow-line {
  opacity: 1;
  clip-path: inset(0 0 0 0);
}

.stage-1 {
  --flow-delay: 40ms;
}

.stage-2 {
  --flow-delay: 120ms;
}

.stage-3 {
  --flow-delay: 200ms;
}

.stage-4 {
  --flow-delay: 280ms;
}

.stage-5 {
  --flow-delay: 360ms;
}

.stage-6 {
  --flow-delay: 440ms;
}

.stage-7 {
  --flow-delay: 520ms;
}

.stage-8 {
  --flow-delay: 600ms;
}

.stage-9 {
  --flow-delay: 680ms;
}

.stage-10 {
  --flow-delay: 760ms;
}

.stage-11 {
  --flow-delay: 840ms;
}

.stage-12 {
  --flow-delay: 920ms;
}

.stage-13 {
  --flow-delay: 980ms;
}

.stage-14 {
  --flow-delay: 1040ms;
}

.inner-node {
  left: 50%;
  width: 140px;
  transform: translateX(-50%);
}

.top-node {
  top: 40px;
}

.bottom-node {
  top: 236px;
}

.single-node {
  width: 130px;
}

.pretrain-node {
  top: 40px;
  left: 205px;
}

.finetune-node {
  top: 40px;
  left: 395px;
}

.inference-node {
  top: 0;
  left: 585px;
}

.monitor-node {
  top: 465px;
  left: 407px;
}

.application-node {
  top: 465px;
  left: 795px;
}

.check-node {
  top: 40px;
  left: 1013px;
}

.leaderboard-node {
  top: 40px;
  left: 1203px;
}

.flow-arrow {
  width: 30px;
}

.arrow-1 {
  top: 72px;
  left: 160px;
}

.arrow-2 {
  top: 72px;
  left: 350px;
}

.arrow-3 {
  top: 72px;
  left: 540px;
}

.arrow-4 {
  top: 72px;
  left: 730px;
}

.arrow-5 {
  top: 72px;
  left: 950px;
}

.arrow-6 {
  top: 72px;
  left: 1150px;
}

.arrow-7 {
  top: 182px;
  left: 266px;
}

.arrow-8 {
  top: 180px;
  left: 286px;
}

.arrow-8 .line-arrow {
  position: absolute;
  top: 14px;
  left: 285px;
}

.arrow-9 {
  top: 230px;
  left: 452px;
}

.arrow-10 {
  top: 281px;
  left: 473px;
}

.flow-mobile-list {
  display: none;
}

.flow-card {
  border: 1px solid rgb(23 98 238 / 10%);
  border-radius: 8px;
  padding: 18px;
  background: rgb(255 255 255 / 86%);
  box-shadow: 0 18px 42px rgb(20 32 92 / 8%);
  opacity: 0;
  transform: translateY(18px);
  transition:
    opacity 280ms ease,
    transform 280ms ease;
  transition-delay: var(--flow-delay, 0ms);
}

.flow-section.is-flow-visible .flow-card {
  opacity: 1;
  transform: translateY(0);
}

.flow-card img {
  width: 52px;
  margin-bottom: 12px;
}

.flow-card p {
  margin-bottom: 2px;
  color: #666;
  font-size: 12px;
  font-weight: 700;
}

.flow-card h3 {
  margin-bottom: 0;
  color: var(--home-title-color);
  font-size: 15px;
  line-height: 20px;
}

.flow-mobile-list {
  width: min(680px, 100%);
  margin: 0 auto;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 1560px) {
  .flow-diagram {
    --flow-scale: 0.8;
  }
}

.flow-section .section-heading {
  margin-bottom: 120px;
}

.flow-section h2 {
  color: var(--home-title-color);
}

/* Keep the full desktop diagram on tablet widths by scaling before switching to cards. */
@media (max-width: 1180px) {
  .flow-diagram {
    --flow-scale: 0.68;
  }
}

@media (max-width: 820px) {
  .flow-section .section-heading {
    margin-bottom: 44px;
  }

  .flow-diagram {
    display: none;
  }

  .flow-mobile-list {
    display: grid;
  }
}

@media (max-width: 1080px) {
  .intro-section {
    padding-bottom: 160px;
  }

  .intro-content {
    margin-bottom: 70px;
  }

  .feature-grid,
  .domain-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .domain-list {
    max-width: 980px;
  }

  .domain-item {
    margin-bottom: 90px;
  }

  .domain-item > h3 {
    margin-bottom: 16px;
    font-size: 20px;
    line-height: 24px;
  }

  .domain-description {
    margin-bottom: 64px;
    font-size: 14px;
    line-height: 20px;
  }

  .domain-card {
    padding: 24px;
  }

  .domain-card h4 {
    margin-bottom: 4px;
    font-size: 14px;
    line-height: 20px;
  }

  .domain-card p {
    font-size: 12px;
    line-height: 16px;
  }
}

@media (max-width: 720px) {
  .hero-section {
    min-height: auto;
  }

  .hero-content {
    width: calc(100% - 32px);
    margin: 0 auto;
    padding: 72px 0 92px;
  }

  .hero-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .primary-action,
  .secondary-action {
    width: 100%;
  }

  .feature-grid,
  .domain-card-grid,
  .flow-mobile-list {
    grid-template-columns: 1fr;
  }

  .intro-section {
    padding-top: 36px;
    padding-bottom: 96px;
  }

  .intro-content {
    margin-bottom: 56px;
  }

  .intro-description {
    font-size: 1rem;
  }

  .feature-icon {
    height: 96px;
  }

  .feature-card h3 {
    font-size: 22px;
    line-height: 26px;
  }

  .domain-item {
    margin-bottom: 72px;
  }

  .domain-description {
    margin-bottom: 36px;
  }
}
</style>
