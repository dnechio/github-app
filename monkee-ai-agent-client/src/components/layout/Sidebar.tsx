import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Tooltip, Divider, IconButton, Typography, Avatar,
} from '@mui/material'
import {
  ChatBubbleOutline, AccountTreeOutlined, AdminPanelSettingsOutlined,
  ChevronLeft, ChevronRight, SmartToyOutlined,
} from '@mui/icons-material'
import { useLocation, useNavigate } from 'react-router-dom'

interface Props {
  width: number
  collapsed: boolean
  onToggle: () => void
}

const NAV_ITEMS = [
  { label: 'Chat', icon: <ChatBubbleOutline />, path: '/chat' },
  { label: 'Pipelines', icon: <AccountTreeOutlined />, path: '/pipeline' },
  { label: 'Admin', icon: <AdminPanelSettingsOutlined />, path: '/admin' },
]

export default function Sidebar({ width, collapsed, onToggle }: Props) {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  return (
    <Drawer
      variant="permanent"
      sx={{
        width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          boxSizing: 'border-box',
          bgcolor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
          transition: 'width 0.2s',
          overflowX: 'hidden',
        },
      }}
    >
      {/* Logo */}
      <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 2, gap: 1.5 }}>
        <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
          <SmartToyOutlined sx={{ fontSize: 18 }} />
        </Avatar>
        {!collapsed && (
          <Typography variant="subtitle2" fontWeight={700} noWrap>
            Criminal Player AI
          </Typography>
        )}
        <Box sx={{ ml: 'auto' }}>
          <IconButton size="small" onClick={onToggle}>
            {collapsed ? <ChevronRight fontSize="small" /> : <ChevronLeft fontSize="small" />}
          </IconButton>
        </Box>
      </Box>

      <Divider />

      <List dense sx={{ px: 1, mt: 1 }}>
        {NAV_ITEMS.map(item => {
          const active = pathname.startsWith(item.path)
          const btn = (
            <ListItemButton
              key={item.path}
              selected={active}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                minHeight: 42,
                justifyContent: collapsed ? 'center' : 'flex-start',
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  '& .MuiListItemIcon-root': { color: 'primary.contrastText' },
                  '&:hover': { bgcolor: 'primary.dark' },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: collapsed ? 0 : 36, color: 'text.secondary' }}>
                {item.icon}
              </ListItemIcon>
              {!collapsed && <ListItemText primary={item.label} />}
            </ListItemButton>
          )

          return collapsed ? (
            <Tooltip key={item.path} title={item.label} placement="right">
              <span>{btn}</span>
            </Tooltip>
          ) : btn
        })}
      </List>
    </Drawer>
  )
}
