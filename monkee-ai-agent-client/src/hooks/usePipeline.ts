import { useCallback, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch, createSSEStream } from '../services/api'
import type { Pipeline, PipelineExecution, StepResult } from '../types'

export function usePipelines() {
  return useQuery<Pipeline[]>({
    queryKey: ['pipelines'],
    queryFn: () => apiFetch('/pipelines/'),
    staleTime: 1000 * 60 * 5,
  })
}

export type PipelineRunState = {
  executionId: string | null
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed'
  steps: StepResult[]
  currentStepId: string | null
  pausePrompt: string | null
  pauseType: 'user_input' | 'file_input' | null
  output: string
}

const INITIAL_STATE: PipelineRunState = {
  executionId: null,
  status: 'idle',
  steps: [],
  currentStepId: null,
  pausePrompt: null,
  pauseType: null,
  output: '',
}

export function usePipelineRunner(pipelineId: string) {
  const [state, setState] = useState<PipelineRunState>(INITIAL_STATE)
  const abortRef = useRef<(() => void) | null>(null)

  const handleEvent = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    const d = event.data as any
    switch (event.type) {
      case 'step_start':
        setState(s => ({
          ...s,
          currentStepId: d.step_id,
          steps: s.steps.map(st =>
            st.step_id === d.step_id ? { ...st, status: 'running' } : st
          ).concat(
            s.steps.find(st => st.step_id === d.step_id)
              ? []
              : [{ step_id: d.step_id, step_name: d.step_name, status: 'running' }]
          ),
        }))
        break
      case 'step_complete':
        setState(s => ({
          ...s,
          steps: s.steps.map(st =>
            st.step_id === d.step_id ? { ...st, status: 'completed', output: d.output_preview } : st
          ),
        }))
        break
      case 'text_delta':
        setState(s => ({ ...s, output: s.output + (d.content ?? '') }))
        break
      case 'pipeline_paused':
        setState(s => ({
          ...s,
          status: 'paused',
          pausePrompt: d.prompt,
          pauseType: d.step_type,
        }))
        break
      case 'pipeline_complete':
        setState(s => ({ ...s, status: 'completed', currentStepId: null }))
        break
      case 'error':
        setState(s => ({ ...s, status: 'failed', output: s.output + `\n\n⚠️ ${d.message}` }))
        break
    }
  }, [])

  const run = useCallback((userParams: Record<string, unknown>) => {
    setState({ ...INITIAL_STATE, status: 'running' })

    abortRef.current = createSSEStream(
      `/pipelines/${pipelineId}/run`,
      { user_params: userParams },
      handleEvent,
      () => setState(s => s.status === 'running' ? { ...s, status: 'completed' } : s),
    )
  }, [pipelineId, handleEvent])

  const resume = useCallback((input: { text?: string; file_id?: string }, executionId: string) => {
    setState(s => ({ ...s, status: 'running', pausePrompt: null, pauseType: null, output: '' }))

    abortRef.current = createSSEStream(
      `/pipelines/executions/${executionId}/resume`,
      input,
      handleEvent,
      () => setState(s => s.status === 'running' ? { ...s, status: 'completed' } : s),
    )
  }, [handleEvent])

  const stop = useCallback(() => {
    abortRef.current?.()
    setState(s => ({ ...s, status: 'failed' }))
  }, [])

  const reset = useCallback(() => setState(INITIAL_STATE), [])

  return { state, run, resume, stop, reset }
}
