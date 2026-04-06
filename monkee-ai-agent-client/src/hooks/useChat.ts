import { useCallback, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { createSSEStream } from '../services/api'
import { useChatStore } from '../store/chat'
import type { Message, SSEEvent } from '../types'

export function useChat(agentId?: string) {
  const {
    sessionId, messages, isStreaming, activeAgent,
    setSessionId, appendMessage, appendDelta, setStreaming, setActiveAgent, reset,
  } = useChatStore()

  const abortRef = useRef<(() => void) | null>(null)

  const send = useCallback((text: string) => {
    if (isStreaming || !text.trim()) return

    const sid = sessionId || uuidv4()
    if (!sessionId) setSessionId(sid)

    const userMsg: Message = {
      id: uuidv4(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    appendMessage(userMsg)

    const assistantMsg: Message = {
      id: uuidv4(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }
    appendMessage(assistantMsg)
    setStreaming(true)

    abortRef.current = createSSEStream(
      '/agents/chat',
      { message: text, session_id: sid, agent_id: agentId ?? null },
      (event: SSEEvent) => {
        switch (event.type) {
          case 'text_delta':
            appendDelta((event.data as any).content ?? '')
            break
          case 'agent_switch':
            setActiveAgent({ name: (event.data as any).agent } as any)
            break
          case 'end':
            setStreaming(false)
            abortRef.current = null
            break
          case 'error':
            appendDelta(`\n\n⚠️ ${(event.data as any).message}`)
            setStreaming(false)
            break
        }
      },
      () => setStreaming(false),
    )
  }, [isStreaming, sessionId, agentId, setSessionId, appendMessage, appendDelta, setStreaming, setActiveAgent])

  const stop = useCallback(() => {
    abortRef.current?.()
    setStreaming(false)
  }, [setStreaming])

  return { messages, isStreaming, activeAgent, send, stop, reset, sessionId }
}
