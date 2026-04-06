import { useState } from 'react'
import {
  Box, Button, TextField, Select, MenuItem, FormControl,
  InputLabel, Switch, FormControlLabel, Typography, Stack,
} from '@mui/material'
import { PlayArrowRounded } from '@mui/icons-material'
import type { Pipeline, PipelineParam } from '../../types'

interface Props {
  pipeline: Pipeline
  onRun: (params: Record<string, unknown>) => void
  onCancel: () => void
}

export default function PipelineParamsForm({ pipeline, onRun, onCancel }: Props) {
  const [values, setValues] = useState<Record<string, unknown>>(() =>
    Object.fromEntries(pipeline.user_params.map(p => [p.key, p.default ?? '']))
  )

  const set = (key: string, val: unknown) => setValues(v => ({ ...v, [key]: val }))

  const canRun = pipeline.user_params
    .filter(p => p.required)
    .every(p => values[p.key] !== '' && values[p.key] != null)

  return (
    <Box>
      <Typography variant="subtitle1" fontWeight={700} gutterBottom>
        Configurar execução
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {pipeline.description}
      </Typography>

      <Stack spacing={2} sx={{ mb: 3 }}>
        {pipeline.user_params.map((param: PipelineParam) => {
          if (param.type === 'select') {
            return (
              <FormControl key={param.key} size="small" fullWidth>
                <InputLabel>{param.label}{param.required ? ' *' : ''}</InputLabel>
                <Select
                  value={values[param.key] ?? ''}
                  label={param.label + (param.required ? ' *' : '')}
                  onChange={e => set(param.key, e.target.value)}
                >
                  {param.options.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            )
          }
          if (param.type === 'boolean') {
            return (
              <FormControlLabel
                key={param.key}
                control={
                  <Switch
                    checked={!!values[param.key]}
                    onChange={e => set(param.key, e.target.checked)}
                  />
                }
                label={param.label}
              />
            )
          }
          return (
            <TextField
              key={param.key}
              label={param.label + (param.required ? ' *' : '')}
              size="small"
              fullWidth
              value={values[param.key] ?? ''}
              onChange={e => set(param.key, e.target.value)}
              required={param.required}
            />
          )
        })}
      </Stack>

      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
        <Button variant="text" onClick={onCancel}>Cancelar</Button>
        <Button
          variant="contained"
          startIcon={<PlayArrowRounded />}
          disabled={!canRun}
          onClick={() => onRun(values)}
        >
          Executar
        </Button>
      </Box>
    </Box>
  )
}
