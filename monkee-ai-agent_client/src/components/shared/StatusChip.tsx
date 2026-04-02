import { Chip, ChipProps } from '@mui/material'

const STATUS_COLORS: Record<string, ChipProps['color']> = {
  ready: 'success',
  completed: 'success',
  running: 'info',
  processing: 'info',
  indexing: 'info',
  queued: 'warning',
  uploading: 'warning',
  paused: 'warning',
  failed: 'error',
  deleted: 'default',
  pending: 'default',
}

const STATUS_LABELS: Record<string, string> = {
  uploading: 'Enviando',
  queued: 'Na fila',
  processing: 'Processando',
  indexing: 'Indexando',
  ready: 'Pronto',
  failed: 'Falhou',
  deleted: 'Deletado',
  running: 'Executando',
  paused: 'Pausado',
  completed: 'Concluído',
  pending: 'Pendente',
}

interface Props {
  status: string
  size?: ChipProps['size']
}

export default function StatusChip({ status, size = 'small' }: Props) {
  return (
    <Chip
      label={STATUS_LABELS[status] ?? status}
      color={STATUS_COLORS[status] ?? 'default'}
      size={size}
      variant="outlined"
    />
  )
}
