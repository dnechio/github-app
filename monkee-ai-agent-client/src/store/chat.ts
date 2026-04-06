import { create } from 'zustand'
import type { Message, Agent } from '../types'

interface ChatStore {
  sessionId: string | null
  messages: Message[]
  activeAgent: Agent | null
  isStreaming: boolean

  setSessionId: (id: string) => void
  appendMessage: (msg: Message) => void
  appendDelta: (delta: string) => void
  setActiveAgent: (agent: Agent | null) => void
  setStreaming: (v: boolean) => void
  reset: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  sessionId: null,
  messages: [],
  activeAgent: null,
  isStreaming: false,

  setSessionId: (id) => set({ sessionId: id }),
  appendMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendDelta: (delta) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last?.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + delta }
      }
      return { messages: msgs }
    }),
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  setStreaming: (v) => set({ isStreaming: v }),
  reset: () => set({ sessionId: null, messages: [], activeAgent: null, isStreaming: false }),
}))
