import { useState } from 'react'
import {
  Box, Button, IconButton, Table, TableBody, TableCell, TableHead, TableRow,
  Typography, Chip, Tooltip, Skeleton,
} from '@mui/material'
import { AddOutlined, EditOutlined, DeleteOutlined, ToggleOnOutlined, ToggleOffOutlined } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../../services/api'
import type { Agent } from '../../../types'
import AgentForm from './AgentForm'

export default function AgentList() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<Agent | null | 'new'>(null)

  const { data: agents, isLoading } = useQuery<Agent[]>({
    queryKey: ['admin', 'agents'],
    queryFn: () => apiFetch('/admin/agents/'),
  })

  const toggleMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/admin/agents/${id}/toggle`, { method: 'PATCH' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'agents'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/admin/agents/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'agents'] }),
  })

  if (editing !== null) {
    return (
      <AgentForm
        agent={editing === 'new' ? undefined : editing}
        onSaved={() => { setEditing(null); qc.invalidateQueries({ queryKey: ['admin', 'agents'] }) }}
        onCancel={() => setEditing(null)}
      />
    )
  }

  return (
    <Box sx={{ p: 3, height: '100%', overflowY: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" fontWeight={700}>Agentes</Typography>
        <Button startIcon={<AddOutlined />} variant="contained" size="small" onClick={() => setEditing('new')}>
          Novo agente
        </Button>
      </Box>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Nome</TableCell>
            <TableCell>Modelo</TableCell>
            <TableCell>Tags</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Ações</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <TableCell key={j}><Skeleton /></TableCell>
                  ))}
                </TableRow>
              ))
            : agents?.map(agent => (
                <TableRow key={agent.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>{agent.name}</Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>{agent.description}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={`${agent.provider}/${agent.model}`} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    {agent.routing_tags?.map(tag => (
                      <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={(agent as any).enabled ? 'Ativo' : 'Inativo'}
                      color={(agent as any).enabled ? 'success' : 'default'}
                      size="small" variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title={(agent as any).enabled ? 'Desativar' : 'Ativar'}>
                      <IconButton size="small" onClick={() => toggleMutation.mutate(agent.id)}>
                        {(agent as any).enabled ? <ToggleOnOutlined color="success" /> : <ToggleOffOutlined />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Editar">
                      <IconButton size="small" onClick={() => setEditing(agent)}>
                        <EditOutlined fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Excluir">
                      <IconButton size="small" color="error" onClick={() => deleteMutation.mutate(agent.id)}>
                        <DeleteOutlined fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Box>
  )
}
