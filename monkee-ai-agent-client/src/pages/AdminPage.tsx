import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from '../components/admin/AdminLayout'
import AgentList from '../components/admin/agents/AgentList'
import MonitoringDashboard from '../components/admin/monitoring/MonitoringDashboard'
import { Box, Typography } from '@mui/material'

const Placeholder = ({ title }: { title: string }) => (
  <Box sx={{ p: 3 }}>
    <Typography variant="h6" fontWeight={700}>{title}</Typography>
    <Typography color="text.secondary" sx={{ mt: 1 }}>Em desenvolvimento.</Typography>
  </Box>
)

export default function AdminPage() {
  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<Navigate to="agents" replace />} />
        <Route path="agents" element={<AgentList />} />
        <Route path="knowledge-bases" element={<Placeholder title="Bases de Conhecimento" />} />
        <Route path="pipelines" element={<Placeholder title="Pipelines" />} />
        <Route path="tools" element={<Placeholder title="Ferramentas" />} />
        <Route path="users" element={<Placeholder title="Usuários" />} />
        <Route path="router" element={<Placeholder title="Roteador" />} />
        <Route path="monitoring" element={<MonitoringDashboard />} />
      </Route>
    </Routes>
  )
}
