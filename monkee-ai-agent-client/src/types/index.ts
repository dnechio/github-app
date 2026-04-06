export interface Agent {
  id: string
  name: string
  slug: string
  description: string
  routing_description: string
  routing_tags: string[]
  model: string
  provider: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agent_id?: string
  created_at: string
  tool_calls?: ToolCall[]
}

export interface ToolCall {
  name: string
  params: Record<string, unknown>
  result?: string
}

export interface Pipeline {
  id: string
  name: string
  slug: string
  description: string
  icon: string
  category: string
  step_count: number
  user_params: PipelineParam[]
  allow_user_customization: boolean
}

export interface PipelineParam {
  key: string
  label: string
  type: 'text' | 'select' | 'boolean'
  options: string[]
  default: unknown
  required: boolean
}

export interface StepResult {
  step_id: string
  step_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  output?: string
}

export interface PipelineExecution {
  id: string
  pipeline_id: string
  status: 'running' | 'paused' | 'completed' | 'failed'
  current_step: number
  steps_results: StepResult[]
}

export interface UserFile {
  id: string
  title: string
  extension: string
  mime_type: string
  bytes: number
  status: 'uploading' | 'queued' | 'processing' | 'indexing' | 'ready' | 'failed' | 'deleted'
  created_at: string
}

export interface SSEEvent {
  type:
    | 'text_delta'
    | 'tool_call_start'
    | 'tool_call_result'
    | 'agent_switch'
    | 'step_start'
    | 'step_complete'
    | 'reasoning_delta'
    | 'memory_loaded'
    | 'pipeline_paused'
    | 'pipeline_complete'
    | 'file_ready'
    | 'error'
    | 'end'
  data: Record<string, unknown>
}
