import { Box, Avatar, Typography, Chip } from '@mui/material'
import { PersonOutlined, SmartToyOutlined } from '@mui/icons-material'
import { motion } from 'framer-motion'
import MarkdownRenderer from '../shared/MarkdownRenderer'
import ToolCallViewer from './ToolCallViewer'
import type { Message } from '../../types'

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function MessageItem({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Box
        sx={{
          display: 'flex',
          gap: 1.5,
          px: 2,
          py: 1.5,
          flexDirection: isUser ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: isUser ? 'secondary.main' : 'primary.main',
            flexShrink: 0,
          }}
        >
          {isUser ? <PersonOutlined sx={{ fontSize: 16 }} /> : <SmartToyOutlined sx={{ fontSize: 16 }} />}
        </Avatar>

        <Box sx={{ maxWidth: '75%', minWidth: 0 }}>
          {message.agent_id && (
            <Chip
              label={message.agent_id}
              size="small"
              variant="outlined"
              sx={{ mb: 0.5, fontSize: 11, height: 20 }}
            />
          )}

          <Box
            sx={{
              bgcolor: isUser ? 'primary.main' : 'background.paper',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              px: 2,
              py: 1.5,
              borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
              border: isUser ? 'none' : '1px solid',
              borderColor: 'divider',
              wordBreak: 'break-word',
            }}
          >
            {message.tool_calls?.length ? (
              <ToolCallViewer toolCalls={message.tool_calls} />
            ) : null}

            {message.content ? (
              isUser ? (
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
              ) : (
                <MarkdownRenderer content={message.content} />
              )
            ) : isStreaming ? (
              <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', py: 0.5 }}>
                {[0, 1, 2].map(i => (
                  <Box
                    key={i}
                    component={motion.div}
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
                    sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main' }}
                  />
                ))}
              </Box>
            ) : null}
          </Box>

          <Typography variant="caption" color="text.disabled" sx={{ mt: 0.25, display: 'block', textAlign: isUser ? 'right' : 'left' }}>
            {new Date(message.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </Typography>
        </Box>
      </Box>
    </motion.div>
  )
}
