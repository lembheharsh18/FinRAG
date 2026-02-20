import axios from 'axios'
import { auth } from './firebase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to all requests
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - try to refresh
      const user = auth.currentUser
      if (user) {
        try {
          const token = await user.getIdToken(true) // Force refresh
          error.config.headers.Authorization = `Bearer ${token}`
          return api.request(error.config)
        } catch {
          // Refresh failed, redirect to login
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

/**
 * Stream an answer from the /api/answer/stream SSE endpoint.
 *
 * @param question  The user's question
 * @param options   Optional params (document_id, n_chunks, temperature)
 * @param onToken   Callback invoked for each token as it arrives
 * @param onDone    Callback invoked when the stream completes
 * @param onError   Callback invoked on error
 */
export async function streamAnswer(
  question: string,
  options: {
    document_id?: string
    n_chunks?: number
    temperature?: number
  },
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void
): Promise<void> {
  const user = auth.currentUser
  const token = user ? await user.getIdToken() : null

  const response = await fetch(`${API_URL}/api/answer/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question,
      document_id: options.document_id ?? null,
      n_chunks: options.n_chunks ?? 5,
      temperature: options.temperature ?? 0.1,
      use_reranking: true,
    }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    onError(errorData.detail?.error || errorData.error || 'Stream request failed')
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError('Streaming not supported')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Parse SSE lines
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.done) {
              onDone()
              return
            }
            if (data.error) {
              onError(data.error)
              return
            }
            if (data.token) {
              onToken(data.token)
            }
          } catch {
            // Ignore malformed JSON lines
          }
        }
      }
    }
    onDone()
  } catch (err) {
    onError(err instanceof Error ? err.message : 'Stream read failed')
  }
}

export default api
