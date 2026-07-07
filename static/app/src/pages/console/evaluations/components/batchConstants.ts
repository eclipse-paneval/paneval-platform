import { i18n } from '@/i18n'

const t = i18n.global.t

export const BATCH_STATUS: Record<
  string,
  { title: string; type: 'info' | 'primary' | 'success' | 'warning' | 'danger' }
> = {
  M: { title: t('status.modified'), type: 'warning' },
  P: { title: t('status.pending'), type: 'warning' },
  PPR: { title: t('status.pending'), type: 'warning' },
  PPE: { title: t('status.pending'), type: 'warning' },
  PST: { title: t('status.starting'), type: 'warning' },
  PSC: { title: t('status.scheduling'), type: 'warning' },
  R: { title: t('status.running'), type: 'primary' },
  DI: { title: t('status.inferenceDone'), type: 'success' },
  HE: { title: t('status.manualEvaluating'), type: 'primary' },
  S: { title: t('status.success'), type: 'success' },
  F: { title: t('status.failure'), type: 'danger' },
  C: { title: t('status.canceled'), type: 'info' },
  default: { title: '-', type: 'info' }
}

export const CAN_STOP_STATUS = ['R', 'PPR', 'PPE', 'PST', 'PSC', 'P']
export const CAN_CONTINUE_STATUS = ['F', 'C', 'M']
export const CAN_EDIT_STATUS = ['F', 'C', 'DI', 'S', 'M']
export const RUNNING_STATUS = ['R', 'PPR', 'PPE', 'PST', 'PSC', 'P', 'HE']

export const batchStatusTitle = (status?: string) =>
  status ? BATCH_STATUS[status]?.title || status : '-'

export const batchStatusType = (status?: string) =>
  status ? BATCH_STATUS[status]?.type || 'info' : 'info'

export const MULTIMODAL_STATUS: Record<
  string,
  { title: string; type: 'info' | 'primary' | 'success' | 'warning' | 'danger' }
> = {
  '-1': { title: t('status.failure'), type: 'danger' },
  '0': { title: t('status.pending'), type: 'warning' },
  '1': { title: t('status.success'), type: 'success' },
  '2': { title: t('status.running'), type: 'primary' },
  '3': { title: t('status.canceled'), type: 'info' },
  '99': { title: t('status.modified'), type: 'warning' },
  default: { title: '-', type: 'info' }
}

export const multimodalStatusTitle = (status?: string) =>
  status ? MULTIMODAL_STATUS[status]?.title || status : '-'

export const multimodalStatusType = (status?: string) =>
  status ? MULTIMODAL_STATUS[status]?.type || 'info' : 'info'
