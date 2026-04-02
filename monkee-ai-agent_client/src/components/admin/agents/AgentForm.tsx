import { useState } from 'react'
import {
  Box, Button, TextField, MenuItem, Select, FormControl, InputLabel,
  Typography, Stack, Switch, FormControlLabel, Divider, Chip,
} from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '../../../services/api'
import type { Agent } from '../../../types'

const PROVIDERS = ['anthropic', 'openai', 'google', 'groq']
const MODELS: Record<string, string[]> = {
  anthropic: ['claude-sonnet-4-6', 'claude-opus-4-6', 'claude-haiku-4-5-20251001'],
  openai: ['gpt-4o', 'gpt-4o-mini', 'o1'],
  google: ['gemini-2.0-flash', 'gemini-1.5-pro'],
  groq: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'],
}

interface Props {
  agent?: Agent
  onSaved: () => void
  onCancel: () => void
}

export default function AgentForm({ agent, onSaved, onCancel }: Props) {
  const isEdit = !!agent

  const [form, setForm] = useState({
    name: agent?.name ?? '',
    slug: agent?.slug ?? '',
    description: agent?.description ?? '',
    provider: agent?.provider ?? 'anthropic',
    model: agent?.model ?? 'claude-sonnet-4-6',
    instructions: (agent as any)?.instructions ?? '',
    temperature: (agent as any)?.temperature ?? 0.7,
    max_tokens: (agent as any)?.max_tokens ?? 4096,
    routing_description: agent?.routing_description ?? '',
    routing_tags: agent?.routing_tags ?? [],
    can_use_user_files: (agent as any)?.can_use_user_files ?? false,
    can_use_memory: (agent as any)?.can_use_memory ?? true,
    show_citations: (agent as any)?.show_citations ?? true,
    enabled: (agent as any)?.enabled ?? true,
  })

  const [tagInput, setTagInput] = useState('')

  const set = (k: string, v: unknown) => setForm(f => ({ ...f, [k]: v }))

  const saveMutation = useMutation({
    mutationFn: () =>
      isEdit
        ? apiFetch(`/admin/agents/${agent!.id}`, { method: 'PUT', body: JSON.stringify(form) })
        : apiFetch('/admin/agents/', { method: 'POST', body: JSON.stringify(form) }),
    onSuccess: onSaved,
  })

  const addTag = () => {
    const t = tagInput.trim()
    if (t && !form.routing_tags.includes(t)) {
      set('routing_tags', [...form.routing_tags, t])
    }
    setTagInput('')
  }

  return (
    <Box sx={{ p: 3, overflowY: 'auto', height: '100%' }}>
      <Typography variant="h6" fontWeight={700} gutterBottom>
        {isEdit ? 'Editar agente' : 'Novo agente'}
      </Typography>

      <Stack spacing={2.5}>
        <Stack direction="row" spacing={2}>
          <TextField label="Nome" size="small" fullWidth value={form.name} onChange={e => set('name', e.target.value)} required />
          <TextField label="Slug" size="small" fullWidth value={form.slug} onChange={e => set('slug', e.target.value)} required />
        </Stack>

        <TextField label="Descrição" size="small" fullWidth value={form.description} onChange={e => set('description', e.target.value)} />

        <Stack direction="row" spacing={2}>
          <FormControl size="small" fullWidth>
            <InputLabel>Provider</InputLabel>
            <Select value={form.provider} label="Provider" onChange={e => { set('provider', e.target.value); set('model', MODELS[e.target.value][0]) }}>
              {PROVIDERS.map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" fullWidth>
            <InputLabel>Modelo</InputLabel>
            <Select value={form.model} label="Modelo" onChange={e => set('model', e.target.value)}>
              {(MODELS[form.provider] ?? []).map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}
            </Select>
          </FormControl>
        </Stack>

        <Stack direction="row" spacing={2}>
          <TextField label="Temperature" size="small" type="number" inputProps={{ step: 0.1, min: 0, max: 2 }} value={form.temperature} onChange={e => set('temperature', parseFloat(e.target.value))} sx={{ width: 160 }} />
          <TextField label="Max tokens" size="small" type="number" value={form.max_tokens} onChange={e => set('max_tokens', parseInt(e.target.value))} sx={{ width: 160 }} />
        </Stack>

        <TextField
          label="Instructions (system prompt)"
          size="small"
          fullWidth
          multiline
          rows={6}
          value={form.instructions}
          onChange={e => set('instructions', e.target.value)}
          placeholder="Você é um especialista em direito penal..."
        />

        <Divider />

        <TextField
          label="Routing description"
          size="small"
          fullWidth
          value={form.routing_description}
          onChange={e => set('routing_description', e.target.value)}
          helperText="Descrição usada pelo RouterAgent para selecionar este agente"
        />

        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>Routing tags</Typography>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {form.routing_tags.map(tag => (
              <Chip
                key={tag} label={tag} size="small"
                onDelete={() => set('routing_tags', form.routing_tags.filter(t => t !== tag))}
              />
            ))}
          </Box>
          <Stack direction="row" spacing={1}>
            <TextField size="small" placeholder="Nova tag" value={tagInput} onChange={e => setTagInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && addTag()} />
            <Button size="small" onClick={addTag}>Adicionar</Button>
          </Stack>
        </Box>

        <Divider />

        <Stack direction="row" spacing={3} flexWrap="wrap">
          <FormControlLabel control={<Switch checked={form.can_use_user_files} onChange={e => set('can_use_user_files', e.target.checked)} />} label="Arquivos do usuário" />
          <FormControlLabel control={<Switch checked={form.can_use_memory} onChange={e => set('can_use_memory', e.target.checked)} />} label="Memória longo prazo" />
          <FormControlLabel control={<Switch checked={form.show_citations} onChange={e => set('show_citations', e.target.checked)} />} label="Mostrar citações" />
          <FormControlLabel control={<Switch checked={form.enabled} onChange={e => set('enabled', e.target.checked)} />} label="Ativo" />
        </Stack>

        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Button variant="text" onClick={onCancel}>Cancelar</Button>
          <Button variant="contained" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            {isEdit ? 'Salvar' : 'Criar'}
          </Button>
        </Box>
      </Stack>
    </Box>
  )
}
