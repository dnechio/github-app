import { Box, Typography, CircularProgress } from '@mui/material'
import {
  CheckCircleOutlined, ErrorOutlined, RadioButtonUncheckedOutlined,
  PauseCircleOutlineOutlined,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import type { StepResult } from '../../types'

interface Props {
  steps: StepResult[]
  currentStepId: string | null
}

const ICON = {
  completed: <CheckCircleOutlined color="success" fontSize="small" />,
  failed: <ErrorOutlined color="error" fontSize="small" />,
  running: <CircularProgress size={16} />,
  paused: <PauseCircleOutlineOutlined color="warning" fontSize="small" />,
  pending: <RadioButtonUncheckedOutlined color="disabled" fontSize="small" />,
  skipped: <RadioButtonUncheckedOutlined color="disabled" fontSize="small" />,
}

export default function StepTracker({ steps, currentStepId }: Props) {
  if (!steps.length) return null

  return (
    <Box sx={{ mb: 2 }}>
      {steps.map((step, i) => (
        <motion.div
          key={step.step_id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 0.75 }}>
            <Box sx={{ flexShrink: 0 }}>
              {ICON[step.status as keyof typeof ICON] ?? ICON.pending}
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography
                variant="body2"
                fontWeight={step.step_id === currentStepId ? 700 : 400}
                noWrap
              >
                {step.step_name}
              </Typography>
              {step.output && step.status === 'completed' && (
                <Typography variant="caption" color="text.secondary" noWrap>
                  {step.output}
                </Typography>
              )}
            </Box>
          </Box>
          {i < steps.length - 1 && (
            <Box sx={{ ml: 1.5, width: 1, height: 12, borderLeft: '1px dashed', borderColor: 'divider' }} />
          )}
        </motion.div>
      ))}
    </Box>
  )
}
