import { i18n } from '@/i18n'

const t = i18n.global.t

const MULTIMODAL_TASK_NAMES: Record<string, string> = {
  图问答: t('multimodal.visualQuestionAnswering'),
  文本生成图像: t('multimodal.textToImageGeneration'),
  '图像-文本匹配': t('multimodal.imageTextMatching'),
  文生视频: t('multimodal.textToVideo'),
  视频理解: t('multimodal.videoUnderstanding'),
  视觉定位: t('multimodal.visualGrounding'),
  指代表达: t('multimodal.referringExpression'),
  文本检索视频: t('multimodal.textToVideoRetrieval'),
  视频文本检索: t('multimodal.videoTextRetrieval'),
  视频问答: t('multimodal.videoQuestionAnswering'),
  色彩理解: t('multimodal.colorUnderstanding'),
  '文本-图像匹配': t('multimodal.textImageMatching')
}

export const MULTIMODAL_TASK_IDS: Record<string, number> = {
  图问答: 11,
  文本生成图像: 12,
  '图像-文本匹配': 13,
  文生视频: 14,
  视频理解: 15
}

export const multimodalTaskName = (name?: unknown) => {
  if (!name) {
    return '-'
  }

  const value = String(name)
  return MULTIMODAL_TASK_NAMES[value] || value
}
