import { describe, expect, it } from 'vitest'
import {
  buildDatasetLabelMap,
  datasetLabels,
  datasetSummary,
  domainLabel,
  sceneLabel
} from './formatters'

describe('evaluation list formatters', () => {
  it('maps scene and domain codes to labels', () => {
    expect(sceneLabel('EA')).toBe('Online evaluation')
    expect(sceneLabel('EM')).toBe('Offline evaluation')
    expect(domainLabel('N')).toBe('NLP')
    expect(domainLabel('A')).toBe('Audio')
    expect(domainLabel('AUDIO')).toBe('Audio')
    expect(domainLabel('S')).toBe('Innovation')
    expect(domainLabel('SF')).toBe('Safety')
    expect(domainLabel('SAFETY')).toBe('Safety')
  })

  it('maps dataset ids to names and prefers multimodal config labels', () => {
    const datasetMap = buildDatasetLabelMap([
      { id: 4, key: 'nlp', scenario: 'NLP Scenario', domain: 'N', name: 'C-Eval' },
      { id: 137, key: 'audio', scenario: 'Audio Scenario', domain: 'A' }
    ])

    expect(datasetLabels([4, 137, 999], datasetMap)).toEqual(['C-Eval', 'Audio Scenario', '999'])
    expect(
      datasetLabels([4], datasetMap, [
        { dataset: 'mm-vqa', datasetShow: 'MM VQA' },
        { dataset: 'mm-caption' }
      ])
    ).toEqual(['MM VQA', 'mm-caption'])
  })

  it('uses safety dataset translations and summaries', () => {
    const datasetMap = buildDatasetLabelMap([
      { id: 1, key: 'safety', scenario: 'Safety Scenario', domain: 'SF', name: 'A.1' },
      { id: 2, key: 'safety', scenario: 'Safety Scenario', domain: 'SF', name: '总体评估' }
    ])

    expect(datasetLabels([1, 2], datasetMap)).toEqual(['Violation of Core Values', 'Overall'])
    expect(datasetSummary([1, 2], datasetMap)).toBe('Violation of Core Values, Overall')
  })
})
