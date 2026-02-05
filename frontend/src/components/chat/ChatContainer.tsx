import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import MessageBubble from './MessageBubble'
import ThinkingIndicator from './ThinkingIndicator'
import { api } from '../../lib/api'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  sources?: Source[]
  timestamp: Date
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

const EXAMPLE_QUESTIONS = [
  "What was the total revenue?",
  "Summarize the key findings",
  "What are the risk factors?"
]

export default function ChatContainer({ documentId, documentName }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

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

  const handleSend = async (question: string = input) => {
    if (!question.trim() || loading) return

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
      const response = await api.post('/api/answer', {
        question: question.trim(),
        document_id: documentId,
        n_chunks: 5,
        use_reranking: true
      })

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-full flex flex-col bg-dark-50/30">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
        <Sparkles className="text-primary" size={20} />
        <div>
          <h2 className="text-white font-medium">Chat with Document</h2>
          <p className="text-gray-400 text-sm">{documentName}</p>
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

        {loading && <ThinkingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Example questions (when empty) */}
      {messages.length === 0 && (
        <div className="px-6 pb-4">
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUESTIONS.map((q, i) => (
              <motion.button
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                onClick={() => handleSend(q)}
                className="glass-hover px-4 py-2 text-sm text-gray-300"
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
            placeholder="Ask a question about this document..."
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
      </div>
    </div>
  )
}
