import { useState } from 'react'
import {
  Box, Button, TextField, Typography, Divider, Paper, IconButton, Tooltip,
} from '@mui/material'
import { StopRounded, RestartAltRounded } from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import StepTracker from './StepTracker'
import MarkdownRenderer from '../shared/MarkdownRenderer'
import FileUploadZone from '../shared/FileUploadZone'
import type { Pipeline } from '../../types'
import { usePipelineRunner } from '../../hooks/usePipeline'

interface Props {
  pipeline: Pipeline
  onBack: () => void
  initialParams: Record<string, unknown>
}

export default function PipelineRunner({ pipeline, onBack, initialParams }: Props) {
  const { state, run, resume, stop, reset } = usePipelineRunner(pipeline.id)
  const [resumeText, setResumeText] = useState('')
  const [uploadLoading, setUploadLoading] = useState(false)

  // Auto-start on mount
  useState(() => { run(initialParams) })

  const handleResumeText = () => {
    if (!state.executionId || !resumeText.trim()) return
    resume({ text: resumeText }, state.executionId)
    setResumeText('')
  }

  const handleResumeFile = async (file: File) => {
    if (!state.executionId) return
    setUploadLoading(true)
    try {
      // Upload file then resume with file_id
      // TODO: wire to file upload flow
      resume({ file_id: 'pending' }, state.executionId)
    } finally {
      setUploadLoading(false)
    }
  }

  const isDone = state.status === 'completed' || state.status === 'failed'
  const isPaused = state.status === 'paused'

  return (
    <Box sx={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Left: step tracker */}
      <Box
        sx={{
          width: 280, flexShrink: 0, p: 2,
          borderRight: '1px solid', borderColor: 'divider',
          overflowY: 'auto',
        }}
      >
        <Typography variant="subtitle2" fontWeight={700} gutterBottom>
          {pipeline.name}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <StepTracker steps={state.steps} currentStepId={state.currentStepId} />

        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          {!isDone && (
            <Tooltip title="Parar">
              <IconButton size="small" color="error" onClick={stop}>
                <StopRounded fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {isDone && (
            <Button size="small" startIcon={<RestartAltRounded />} onClick={() => { reset(); run(initialParams) }}>
              Executar novamente
            </Button>
          )}
          <Button size="small" variant="text" onClick={onBack}>Voltar</Button>
        </Box>
      </Box>

      {/* Right: output + pause prompt */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Output */}
        <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
          <AnimatePresence>
            {state.output && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                  <MarkdownRenderer content={state.output} />
                </Paper>
              </motion.div>
            )}
          </AnimatePresence>
        </Box>

        {/* Pause prompt */}
        <AnimatePresence>
          {isPaused && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
              <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  {state.pausePrompt}
                </Typography>

                {state.pauseType === 'file_input' ? (
                  <FileUploadZone onFile={handleResumeFile} loading={uploadLoading} />
                ) : (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="Sua resposta…"
                      value={resumeText}
                      onChange={e => setResumeText(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleResumeText()}
                    />
                    <Button variant="contained" onClick={handleResumeText} disabled={!resumeText.trim()}>
                      Continuar
                    </Button>
                  </Box>
                )}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    </Box>
  )
}
