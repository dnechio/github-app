import { useState } from 'react'
import {
  Box, Card, CardContent, Grid, Typography, Table, TableBody,
  TableCell, TableHead, TableRow, Select, MenuItem, Skeleton,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../../services/api'

type Period = 'day' | 'week' | 'month'

export default function MonitoringDashboard() {
  const [period, setPeriod] = useState<Period>('day')

  const { data: stats } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => apiFetch('/admin/monitoring/stats'),
  })

  const { data: usage, isLoading: usageLoading } = useQuery({
    queryKey: ['admin', 'usage', period],
    queryFn: () => apiFetch(`/admin/monitoring/usage?period=${period}`),
  })

  const { data: errors, isLoading: errorsLoading } = useQuery({
    queryKey: ['admin', 'errors'],
    queryFn: () => apiFetch('/admin/monitoring/errors'),
  })

  return (
    <Box sx={{ p: 3, overflowY: 'auto', height: '100%' }}>
      <Typography variant="h6" fontWeight={700} gutterBottom>Monitoramento</Typography>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { label: 'Agentes', value: stats?.agents },
          { label: 'Bases de Conhecimento', value: stats?.knowledge_bases },
          { label: 'Pipelines', value: stats?.pipelines },
          { label: 'Usuários', value: stats?.users },
        ].map(s => (
          <Grid item xs={6} sm={3} key={s.label}>
            <Card variant="outlined">
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="h4" fontWeight={700}>
                  {s.value ?? <Skeleton width={40} />}
                </Typography>
                <Typography variant="caption" color="text.secondary">{s.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Usage */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Typography variant="subtitle2" fontWeight={700}>Uso por agente</Typography>
        <FormControl size="small" sx={{ width: 120 }}>
          <Select value={period} onChange={e => setPeriod(e.target.value as Period)}>
            <MenuItem value="day">Hoje</MenuItem>
            <MenuItem value="week">Semana</MenuItem>
            <MenuItem value="month">Mês</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Table size="small" sx={{ mb: 3 }}>
        <TableHead>
          <TableRow>
            <TableCell>Agente</TableCell>
            <TableCell align="right">Chamadas</TableCell>
            <TableCell align="right">Tokens entrada</TableCell>
            <TableCell align="right">Tokens saída</TableCell>
            <TableCell align="right">Usuários únicos</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {usageLoading
            ? Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>{Array.from({ length: 5 }).map((_, j) => <TableCell key={j}><Skeleton /></TableCell>)}</TableRow>
              ))
            : (usage as any[])?.map((row: any) => (
                <TableRow key={row.agent_id} hover>
                  <TableCell>{row.agent_id}</TableCell>
                  <TableCell align="right">{row.total_calls}</TableCell>
                  <TableCell align="right">{row.total_input_tokens?.toLocaleString()}</TableCell>
                  <TableCell align="right">{row.total_output_tokens?.toLocaleString()}</TableCell>
                  <TableCell align="right">{row.unique_users}</TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>

      {/* Recent errors */}
      <Typography variant="subtitle2" fontWeight={700} gutterBottom>Erros recentes</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Mensagem</TableCell>
            <TableCell>Agente</TableCell>
            <TableCell>Data</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {errorsLoading
            ? Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>{Array.from({ length: 3 }).map((_, j) => <TableCell key={j}><Skeleton /></TableCell>)}</TableRow>
              ))
            : (errors as any[])?.map((e: any, i) => (
                <TableRow key={i} hover>
                  <TableCell sx={{ maxWidth: 400 }}>
                    <Typography variant="caption" noWrap>{e.message}</Typography>
                  </TableCell>
                  <TableCell>{e.agent_id}</TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(e.created_at).toLocaleString('pt-BR')}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Box>
  )
}

