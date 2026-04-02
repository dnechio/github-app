import { useState } from 'react'
import { Box, Collapse, IconButton, Typography, Paper } from '@mui/material'
import { ExpandMore, ExpandLess, BuildOutlined } from '@mui/icons-material'
import type { ToolCall } from '../../types'

interface Props {
  toolCalls: ToolCall[]
}

export default function ToolCallViewer({ toolCalls }: Props) {
  const [open, setOpen] = useState(false)
  if (!toolCalls.length) return null

  return (
    <Box sx={{ mb: 1 }}>
      <Box
        onClick={() => setOpen(o => !o)}
        sx={{ display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer', color: 'text.secondary' }}
      >
        <BuildOutlined sx={{ fontSize: 14 }} />
        <Typography variant="caption">{toolCalls.length} ferramenta(s) usada(s)</Typography>
        <IconButton size="small" sx={{ p: 0 }}>
          {open ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </IconButton>
      </Box>
      <Collapse in={open}>
        {toolCalls.map((tc, i) => (
          <Paper
            key={i}
            variant="outlined"
            sx={{ mt: 0.5, p: 1.5, bgcolor: 'action.hover', fontFamily: 'monospace', fontSize: 12 }}
          >
            <Typography variant="caption" fontWeight={700} color="primary.main">
              {tc.name}
            </Typography>
            {tc.result && (
              <Box sx={{ mt: 0.5, color: 'text.secondary', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result, null, 2)}
              </Box>
            )}
          </Paper>
        ))}
      </Collapse>
    </Box>
  )
}
