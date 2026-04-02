import { Card, CardActionArea, CardContent, Typography, Chip, Box } from '@mui/material'
import { AccountTreeOutlined } from '@mui/icons-material'
import type { Pipeline } from '../../types'

interface Props {
  pipeline: Pipeline
  onClick: () => void
}

export default function PipelineCard({ pipeline, onClick }: Props) {
  return (
    <Card variant="outlined" sx={{ height: '100%', '&:hover': { borderColor: 'primary.main' } }}>
      <CardActionArea onClick={onClick} sx={{ height: '100%', alignItems: 'flex-start' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
            <Box
              sx={{
                width: 40, height: 40, borderRadius: 2,
                bgcolor: 'primary.main', display: 'flex',
                alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}
            >
              <AccountTreeOutlined sx={{ color: '#fff', fontSize: 20 }} />
            </Box>
            <Box>
              <Typography variant="subtitle2" fontWeight={700}>{pipeline.name}</Typography>
              <Chip label={pipeline.category} size="small" sx={{ height: 18, fontSize: 10 }} />
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {pipeline.description}
          </Typography>
          <Typography variant="caption" color="text.disabled">
            {pipeline.step_count} etapas
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
