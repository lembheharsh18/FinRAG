import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, RotateCcw, Loader2, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import MessageBubble from './MessageBubble'
import ThinkingIndicator from './ThinkingIndicator'
import ExportButton from './ExportButton'
import { api } from '../../lib/api'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  sources?: Source[]
  timestamp: Date
  streaming?: boolean
}

interface Source {
  page_number: number
  chunk_type: string
  section_header?: string
  content_preview: string
}

interface ChatContainerProps {
  documentId: string
  documentName: string
}

export default function ChatContainer({ documentId, documentName }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [useStreaming, setUseStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [documentId])

  // Fetch smart suggestions when document changes
  useEffect(() => {
    fetchSuggestions()
    // Reset chat on document change
    setMessages([])
    setSessionId(null)
  }, [documentId])

  const fetchSuggestions = async () => {
    setLoadingSuggestions(true)
    try {
      const response = await api.get(`/api/documents/${documentId}/suggestions`)
      setSuggestions(response.data.suggestions || [])
    } catch (err) {
      console.log('Could not load suggestions, using defaults')
      setSuggestions([
        "What are the key financial highlights?",
        "What is the total revenue reported?",
        "What are the main risk factors?",
        "How did the company perform this year?"
      ])
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const handleSendStreaming = async (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: question.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Create a placeholder AI message for streaming
    const aiMessageId = (Date.now() + 1).toString()
    const aiMessage: Message = {
      id: aiMessageId,
      type: 'ai',
      content: '',
      timestamp: new Date(),
      streaming: true
    }
    setMessages(prev => [...prev, aiMessage])

    try {
      abortControllerRef.current = new AbortController()
      
      // Get auth token
      const { auth } = await import('../../lib/firebase')
      const user = auth.currentUser
      const token = user ? await user.getIdToken() : ''

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question: question.trim(),
          document_id: documentId,
          n_chunks: 5
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) throw new Error('Stream request failed')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let sources: Source[] = []

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const text = decoder.decode(value, { stream: true })
          const lines = text.split('\n\n').filter(line => line.startsWith('data: '))

          for (const line of lines) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'sources') {
                sources = data.sources
              } else if (data.type === 'token') {
                setMessages(prev => prev.map(m => 
                  m.id === aiMessageId 
                    ? { ...m, content: m.content + data.content }
                    : m
                ))
              } else if (data.type === 'done') {
                setMessages(prev => prev.map(m => 
                  m.id === aiMessageId 
                    ? { ...m, streaming: false, sources }
                    : m
                ))
              } else if (data.type === 'error') {
                throw new Error(data.message)
              }
            } catch (parseErr) {
              // Skip malformed SSE lines
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return
      console.error('Stream error:', error)
      setMessages(prev => prev.map(m => 
        m.id === aiMessageId 
          ? { ...m, content: 'Sorry, I encountered an error. Please try again.', streaming: false }
          : m
      ))
      toast.error('Failed to get answer')
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }

  const handleSendConversation = async (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: question.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await api.post('/api/chat/conversation', {
        question: question.trim(),
        document_id: documentId,
        session_id: sessionId,
        n_chunks: 5
      })

      setSessionId(response.data.session_id)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error: any) {
      console.error('Query error:', error)
      toast.error(error.response?.data?.detail?.error || 'Failed to get answer')
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async (question: string = input) => {
    if (!question.trim() || loading) return

    if (useStreaming) {
      await handleSendStreaming(question)
    } else {
      await handleSendConversation(question)
    }
  }

  const handleNewChat = async () => {
    if (sessionId) {
      try {
        await api.delete(`/api/chat/conversation/${sessionId}`)
      } catch {}
    }
    setMessages([])
    setSessionId(null)
    fetchSuggestions()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-full flex flex-col bg-dark-50/30">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="text-primary" size={20} />
          <div>
            <h2 className="text-white font-medium">Chat with Document</h2>
            <p className="text-gray-400 text-sm">{documentName}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Streaming toggle */}
          <button
            onClick={() => setUseStreaming(!useStreaming)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              useStreaming 
                ? 'bg-primary/20 text-primary border border-primary/30' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
            title={useStreaming ? 'Streaming mode (real-time)' : 'Standard mode (with memory)'}
          >
            <Zap size={12} />
            {useStreaming ? 'Stream' : 'Memory'}
          </button>
          {/* Export button */}
          {messages.length > 0 && (
            <ExportButton 
              documentId={documentId} 
              documentName={documentName} 
              messages={messages.map(m => ({ type: m.type, content: m.content, sources: m.sources }))}
            />
          )}
          {/* New chat button */}
          {messages.length > 0 && (
            <button
              onClick={handleNewChat}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all"
            >
              <RotateCcw size={12} />
              New Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Sparkles className="mx-auto text-gray-600 mb-4" size={40} />
              <p className="text-gray-400 mb-2">Ask a question about this document</p>
              <p className="text-gray-500 text-sm">
                I'll find relevant information and provide cited answers
              </p>
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </AnimatePresence>
        )}

        {loading && !messages.some(m => m.streaming) && <ThinkingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Smart suggestions (when empty) */}
      {messages.length === 0 && (
        <div className="px-6 pb-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} className="text-primary" />
            <span className="text-xs text-gray-400 font-medium">
              {loadingSuggestions ? 'Generating smart questions...' : 'Suggested questions'}
            </span>
            {loadingSuggestions && <Loader2 size={12} className="animate-spin text-primary" />}
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((q, i) => (
              <motion.button
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                onClick={() => handleSend(q)}
                className="glass-hover px-4 py-2 text-sm text-gray-300 hover:text-white hover:border-primary/30 transition-all"
              >
                {q}
              </motion.button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="p-6 border-t border-white/5">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={useStreaming ? "Ask a question (streaming mode)..." : "Ask a question (with memory)..."}
            className="input-field flex-1"
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="btn-primary px-4"
          >
            <Send size={18} />
          </button>
        </div>
        {!useStreaming && sessionId && (
          <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Conversation memory active · {messages.filter(m => m.type === 'user').length} messages
          </p>
        )}
      </div>
    </div>
  )
}
