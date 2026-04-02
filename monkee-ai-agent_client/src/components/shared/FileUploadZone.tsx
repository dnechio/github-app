import { useRef, useState } from 'react'
import { Box, Typography, CircularProgress } from '@mui/material'
import { CloudUploadOutlined } from '@mui/icons-material'

interface Props {
  onFile: (file: File) => void
  accept?: string
  loading?: boolean
  label?: string
}

export default function FileUploadZone({
  onFile,
  accept = '*/*',
  loading = false,
  label = 'Arraste um arquivo ou clique para selecionar',
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handle = (file: File | null) => {
    if (file) onFile(file)
  }

  return (
    <Box
      onClick={() => !loading && inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => {
        e.preventDefault()
        setDragging(false)
        handle(e.dataTransfer.files[0] ?? null)
      }}
      sx={{
        border: '2px dashed',
        borderColor: dragging ? 'primary.main' : 'divider',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: loading ? 'default' : 'pointer',
        bgcolor: dragging ? 'action.hover' : 'transparent',
        transition: 'all 0.15s',
        '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' },
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        style={{ display: 'none' }}
        onChange={e => handle(e.target.files?.[0] ?? null)}
      />
      {loading ? (
        <CircularProgress size={32} />
      ) : (
        <>
          <CloudUploadOutlined sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
          <Typography variant="body2" color="text.secondary">{label}</Typography>
        </>
      )}
    </Box>
  )
}
