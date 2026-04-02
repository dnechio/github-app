import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../services/api'
import type { Agent } from '../types'

export function useAgents() {
  return useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => apiFetch('/agents/'),
    staleTime: 1000 * 60 * 5,
  })
}
