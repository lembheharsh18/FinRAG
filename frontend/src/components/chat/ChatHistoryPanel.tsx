import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { History, MessageSquare, Trash2, Plus, Loader2 } from 'lucide-react'
import { api } from '../../lib/api'

interface Session {
  session_id: string
  document_id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

interface ChatHistoryPanelProps {
  documentId: string
  currentSessionId: string | null
  onSelectSession: (sessionId: string) => void
  onNewSession: (sessionId: string) => void
  isOpen: boolean
  onToggle: () => void
}

export default function ChatHistoryPanel({
  documentId,
  currentSessionId,
  onSelectSession,
  onNewSession,
  isOpen,
  onToggle
}: ChatHistoryPanelProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadSessions()
    }
  }, [isOpen, documentId])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const resp = await api.get(`/api/chat/sessions/${documentId}`)
      setSessions(resp.data)
    } catch {
      setSessions([])
    } finally {
      setLoading(false)
    }
  }

  const createNewSession = async () => {
    try {
      const resp = await api.post(`/api/chat/sessions/${documentId}`)
      onNewSession(resp.data.session_id)
      loadSessions()
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.delete(`/api/chat/sessions/${documentId}/${sessionId}`)
      setSessions(prev => prev.filter(s => s.session_id !== sessionId))
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-white hover:bg-white/5 transition-all"
        title="Chat History"
      >
        <History size={14} />
        <span>History</span>
      </button>

      {/* Slide-out panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/30 z-40"
              onClick={onToggle}
            />

            {/* Panel */}
            <motion.div
              initial={{ x: -320, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -320, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 h-full w-80 glass z-50 flex flex-col border-r border-white/10"
            >
              {/* Header */}
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <History size={18} className="text-primary" />
                  Chat History
                </h3>
                <button
                  onClick={createNewSession}
                  className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-primary transition-colors"
                  title="New Chat"
                >
                  <Plus size={18} />
                </button>
              </div>

              {/* Sessions list */}
              <div className="flex-1 overflow-y-auto p-2">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 size={24} className="animate-spin text-gray-400" />
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="text-center py-12 px-4">
                    <MessageSquare size={32} className="mx-auto text-gray-600 mb-3" />
                    <p className="text-sm text-gray-500">No chat history yet</p>
                    <p className="text-xs text-gray-600 mt-1">Start chatting to create your first session</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {sessions.map(session => (
                      <motion.button
                        key={session.session_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        onClick={() => onSelectSession(session.session_id)}
                        className={`w-full group flex items-start gap-3 p-3 rounded-xl transition-all text-left ${
                          currentSessionId === session.session_id
                            ? 'bg-primary/10 border border-primary/20'
                            : 'hover:bg-white/5'
                        }`}
                      >
                        <MessageSquare size={16} className={`mt-0.5 flex-shrink-0 ${
                          currentSessionId === session.session_id ? 'text-primary' : 'text-gray-500'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${
                            currentSessionId === session.session_id ? 'text-primary' : 'text-gray-300'
                          }`}>
                            {session.title}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500">{session.message_count} messages</span>
                            <span className="text-xs text-gray-600">•</span>
                            <span className="text-xs text-gray-500">{formatDate(session.updated_at)}</span>
                          </div>
                        </div>
                        
                        <button
                          onClick={(e) => deleteSession(session.session_id, e)}
                          className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-all"
                        >
                          <Trash2 size={12} />
                        </button>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-3 border-t border-white/5">
                <button
                  onClick={createNewSession}
                  className="w-full btn-primary text-sm flex items-center justify-center gap-2"
                >
                  <Plus size={16} />
                  New Chat Session
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
