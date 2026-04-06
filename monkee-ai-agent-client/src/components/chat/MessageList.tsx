import { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import MessageItem from './MessageItem'
import type { Message } from '../../types'

interface Props {
  messages: Message[]
  isStreaming: boolean
}

export default function MessageList({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <Box sx={{ flex: 1, overflowY: 'auto', py: 1 }}>
      {messages.map((msg, i) => (
        <MessageItem
          key={msg.id}
          message={msg}
          isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
        />
      ))}
      <div ref={bottomRef} />
    </Box>
  )
}
