import { useState } from 'react'
import { Box, Grid, Typography, TextField, InputAdornment, Skeleton, Dialog, DialogContent } from '@mui/material'
import { SearchOutlined } from '@mui/icons-material'
import { AnimatePresence, motion } from 'framer-motion'
import PipelineCard from './PipelineCard'
import PipelineParamsForm from './PipelineParamsForm'
import PipelineRunner from './PipelineRunner'
import { usePipelines } from '../../hooks/usePipeline'
import type { Pipeline } from '../../types'

type View = { mode: 'gallery' } | { mode: 'params'; pipeline: Pipeline } | { mode: 'run'; pipeline: Pipeline; params: Record<string, unknown> }

export default function PipelineGallery() {
  const { data: pipelines, isLoading } = usePipelines()
  const [search, setSearch] = useState('')
  const [view, setView] = useState<View>({ mode: 'gallery' })

  const filtered = (pipelines ?? []).filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.description.toLowerCase().includes(search.toLowerCase())
  )

  if (view.mode === 'run') {
    return (
      <PipelineRunner
        pipeline={view.pipeline}
        initialParams={view.params}
        onBack={() => setView({ mode: 'gallery' })}
      />
    )
  }

  return (
    <Box sx={{ p: 3, height: '100%', overflowY: 'auto' }}>
      <Typography variant="h6" fontWeight={700} gutterBottom>Pipelines</Typography>

      <TextField
        size="small"
        placeholder="Buscar pipelines…"
        value={search}
        onChange={e => setSearch(e.target.value)}
        sx={{ mb: 3, width: 320 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchOutlined fontSize="small" />
            </InputAdornment>
          ),
        }}
      />

      {isLoading ? (
        <Grid container spacing={2}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={140} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Grid container spacing={2}>
          {filtered.map(p => (
            <Grid item xs={12} sm={6} md={4} key={p.id}>
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <PipelineCard
                  pipeline={p}
                  onClick={() =>
                    p.user_params.length > 0 && p.allow_user_customization
                      ? setView({ mode: 'params', pipeline: p })
                      : setView({ mode: 'run', pipeline: p, params: {} })
                  }
                />
              </motion.div>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Params dialog */}
      <Dialog
        open={view.mode === 'params'}
        onClose={() => setView({ mode: 'gallery' })}
        maxWidth="xs"
        fullWidth
      >
        <DialogContent>
          {view.mode === 'params' && (
            <PipelineParamsForm
              pipeline={view.pipeline}
              onRun={params => setView({ mode: 'run', pipeline: view.pipeline, params })}
              onCancel={() => setView({ mode: 'gallery' })}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}
