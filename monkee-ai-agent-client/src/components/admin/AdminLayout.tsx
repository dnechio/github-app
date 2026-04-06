import { Box, List, ListItemButton, ListItemIcon, ListItemText, Typography, Divider } from '@mui/material'
import {
  SmartToyOutlined, LibraryBooksOutlined, AccountTreeOutlined,
  BuildOutlined, PeopleOutlined, BarChartOutlined, AltRouteOutlined,
} from '@mui/icons-material'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

const ADMIN_NAV = [
  { label: 'Agentes', icon: <SmartToyOutlined />, path: '/admin/agents' },
  { label: 'Bases de Conhecimento', icon: <LibraryBooksOutlined />, path: '/admin/knowledge-bases' },
  { label: 'Pipelines', icon: <AccountTreeOutlined />, path: '/admin/pipelines' },
  { label: 'Ferramentas', icon: <BuildOutlined />, path: '/admin/tools' },
  { label: 'Usuários', icon: <PeopleOutlined />, path: '/admin/users' },
  { label: 'Roteador', icon: <AltRouteOutlined />, path: '/admin/router' },
  { label: 'Monitoramento', icon: <BarChartOutlined />, path: '/admin/monitoring' },
]

export default function AdminLayout() {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      {/* Sub-sidebar */}
      <Box
        sx={{
          width: 220, flexShrink: 0, borderRight: '1px solid', borderColor: 'divider',
          p: 1, overflowY: 'auto',
        }}
      >
        <Typography variant="overline" sx={{ px: 1, color: 'text.secondary', fontWeight: 700 }}>
          Admin
        </Typography>
        <Divider sx={{ my: 1 }} />
        <List dense>
          {ADMIN_NAV.map(item => (
            <ListItemButton
              key={item.path}
              selected={pathname.startsWith(item.path)}
              onClick={() => navigate(item.path)}
              sx={{ borderRadius: 1.5, mb: 0.25 }}
            >
              <ListItemIcon sx={{ minWidth: 32, color: 'text.secondary' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ variant: 'body2' }} />
            </ListItemButton>
          ))}
        </List>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Outlet />
      </Box>
    </Box>
  )
}
