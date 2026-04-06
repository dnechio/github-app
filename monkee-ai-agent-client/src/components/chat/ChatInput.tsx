import { useState, useRef, KeyboardEvent } from 'react'
import { Box, IconButton, TextField, Tooltip, CircularProgress } from '@mui/material'
import { SendRounded, StopRounded, AttachFileOutlined } from '@mui/icons-material'

interface Props {
  onSend: (text: string) => void
  onStop: () => void
  onAttach?: (file: File) => void
  isStreaming: boolean
  disabled?: boolean
}

export default function ChatInput({ onSend, onStop, onAttach, isStreaming, disabled }: Props) {
  const [text, setText] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const submit = () => {
    const t = text.trim()
    if (!t || isStreaming) return
    onSend(t)
    setText('')
  }

  const handleKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <Box
      sx={{
        px: 2, py: 1.5,
        borderTop: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        display: 'flex',
        gap: 1,
        alignItems: 'flex-end',
      }}
    >
      <input
        ref={fileRef}
        type="file"
        style={{ display: 'none' }}
        onChange={e => onAttach?.(e.target.files![0])}
      />

      {onAttach && (
        <Tooltip title="Anexar arquivo">
          <IconButton size="small" onClick={() => fileRef.current?.click()} disabled={isStreaming || disabled}>
            <AttachFileOutlined fontSize="small" />
          </IconButton>
        </Tooltip>
      )}

      <TextField
        fullWidth
        multiline
        maxRows={6}
        size="small"
        placeholder="Digite sua mensagem… (Shift+Enter para nova linha)"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKey}
        disabled={isStreaming || disabled}
        variant="outlined"
        sx={{
          '& .MuiOutlinedInput-root': { borderRadius: 3 },
        }}
      />

      {isStreaming ? (
        <Tooltip title="Parar">
          <IconButton color="error" onClick={onStop}>
            <StopRounded />
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title="Enviar (Enter)">
          <span>
            <IconButton
              color="primary"
              onClick={submit}
              disabled={!text.trim() || disabled}
            >
              <SendRounded />
            </IconButton>
          </span>
        </Tooltip>
      )}
    </Box>
  )
}
