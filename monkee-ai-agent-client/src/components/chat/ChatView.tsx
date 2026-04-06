import { useState } from 'react'
import { Box, Toolbar, Chip, Typography, Tooltip, IconButton } from '@mui/material'
import { DeleteOutline, SmartToyOutlined } from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import AgentSelector from './AgentSelector'
import { useChat } from '../../hooks/useChat'

export default function ChatView() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const { messages, isStreaming, activeAgent, send, stop, reset } = useChat(selectedAgent ?? undefined)

  const isEmpty = messages.length === 0

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <Toolbar
        variant="dense"
        sx={{
          borderBottom: '1px solid',
          borderColor: 'divider',
          gap: 1,
          minHeight: 52,
        }}
      >
        <AgentSelector value={selectedAgent} onChange={setSelectedAgent} />

        {activeAgent && (
          <Chip
            icon={<SmartToyOutlined sx={{ fontSize: 14 }} />}
            label={activeAgent.name}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Nova conversa">
          <span>
            <IconButton size="small" onClick={reset} disabled={isEmpty}>
              <DeleteOutline fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      </Toolbar>

      {/* Empty state */}
      <AnimatePresence>
        {isEmpty && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <Box textAlign="center" sx={{ color: 'text.secondary' }}>
              <SmartToyOutlined sx={{ fontSize: 56, mb: 1, opacity: 0.4 }} />
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Como posso ajudar?
              </Typography>
              <Typography variant="body2" sx={{ maxWidth: 380 }}>
                Escolha um agente acima ou deixe o roteador selecionar automaticamente.
              </Typography>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      {!isEmpty && (
        <MessageList messages={messages} isStreaming={isStreaming} />
      )}

      {/* Input */}
      <ChatInput onSend={send} onStop={stop} isStreaming={isStreaming} />
    </Box>
  )
}
