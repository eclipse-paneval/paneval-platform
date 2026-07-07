import { i18n } from '@/i18n'

const t = i18n.global.t

export const imageLabels = {
  page: t('images.page'),
  presetImages: t('images.presetImages'),
  customImagesLabel: t('images.customImages'),
  importImages: t('images.importImages'),
  id: t('images.id'),
  name: t('common.name'),
  tag: t('images.tag'),
  registryUrl: t('images.registryUrl'),
  status: t('common.status'),
  first: t('images.first'),
  second: t('images.second'),
  createdTime: t('images.createdTime'),
  creator: t('images.creator'),
  action: t('common.action'),
  keywordsPlaceholder: t('images.keywordsPlaceholder'),
  createTitle: t('images.createTitle'),
  url: t('images.url'),
  urlDescription: t('images.urlDescription'),
  dockerfilePlaceholder: t('images.dockerfilePlaceholder'),
  dockerfileDescription: t('images.dockerfileDescription'),
  imageDesc: t('images.imageDesc'),
  submitSuccessMessage: t('images.submitSuccessMessage'),
  actionDeleteMessage: t('images.actionDeleteMessage'),
  dockerFileTitle: t('images.dockerFileTitle'),
  dockerfile: t('images.dockerfile'),
  check: t('images.checkCommand'),
  approveMessage: t('images.approveMessage'),
  denyMessage: t('images.denyMessage'),
  source: t('images.source'),
  nameTip: t('images.nameTip'),
  notLatest: t('images.notLatest'),
  customEmptyDescription: t('images.customEmptyDescription'),
  customEmptyInformation: t('images.customEmptyInformation'),
  customEmptyAction: t('images.customEmptyAction'),
  document: t('images.document'),
  denyTitle: t('images.denyTitle'),
  importTip: t('images.importTip')
}

export const importMethods: Record<string, string> = {
  P: t('images.publicImageRepository'),
  F: t('images.terminalCommand')
}

export const imageStatus: Record<string, string> = {
  P: t('images.auditing'),
  PC: t('images.importing'),
  PF: t('images.importFailed'),
  R: t('images.importSuccess'),
  D: t('images.denied'),
  C: t('images.canceled')
}

export const imageStatusStage: Record<string, string> = {
  P: t('images.auditing'),
  PC: t('images.importing'),
  PF: t('images.importFailed'),
  R: t('common.success'),
  D: t('images.denied'),
  C: t('images.canceled')
}

export const imageStatusType = (
  status?: string
): 'info' | 'primary' | 'success' | 'warning' | 'danger' => {
  const map: Record<string, 'info' | 'primary' | 'success' | 'warning' | 'danger'> = {
    P: 'warning',
    PC: 'primary',
    PF: 'danger',
    R: 'success',
    D: 'danger',
    C: 'info'
  }

  return status ? map[status] || 'info' : 'info'
}
