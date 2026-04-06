import {
  Box, MenuItem, Select, FormControl, InputLabel, Chip, Typography, Skeleton,
} from '@mui/material'
import { useAgents } from '../../hooks/useAgents'
import type { Agent } from '../../types'

interface Props {
  value: string | null
  onChange: (agentId: string | null) => void
}

export default function AgentSelector({ value, onChange }: Props) {
  const { data: agents, isLoading } = useAgents()

  if (isLoading) return <Skeleton width={220} height={40} />

  return (
    <FormControl size="small" sx={{ minWidth: 220 }}>
      <InputLabel>Agente</InputLabel>
      <Select
        value={value ?? '__auto__'}
        label="Agente"
        onChange={e => onChange(e.target.value === '__auto__' ? null : e.target.value)}
      >
        <MenuItem value="__auto__">
          <Box>
            <Typography variant="body2" fontWeight={600}>Automático</Typography>
            <Typography variant="caption" color="text.secondary">RouterAgent seleciona</Typography>
          </Box>
        </MenuItem>
        {agents?.map((agent: Agent) => (
          <MenuItem key={agent.id} value={agent.id}>
            <Box>
              <Typography variant="body2" fontWeight={600}>{agent.name}</Typography>
              <Typography variant="caption" color="text.secondary" noWrap>{agent.routing_description}</Typography>
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}
