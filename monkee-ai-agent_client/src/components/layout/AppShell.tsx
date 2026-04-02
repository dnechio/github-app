import { useState } from 'react'
import { Box } from '@mui/material'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

const SIDEBAR_WIDTH = 260

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const width = collapsed ? 64 : SIDEBAR_WIDTH

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
      <Sidebar width={width} collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <Box
        component="main"
        sx={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          transition: 'margin 0.2s',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}
