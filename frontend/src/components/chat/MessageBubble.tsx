import { useState } from 'react'
import { motion } from 'framer-motion'
import { Copy, ThumbsUp, ThumbsDown, Check, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

interface Source {
  page_number: number
  chunk_type: string
  section_header?: string
  content_preview: string
}

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  sources?: Source[]
  timestamp: Date
}

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const [showSources, setShowSources] = useState(false)

  const isUser = message.type === 'user'

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  const handleFeedback = (type: 'up' | 'down') => {
    setFeedback(type)
    toast.success('Thanks for your feedback!')
    // TODO: Send feedback to backend
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[80%] ${isUser ? 'order-2' : ''}`}>
        {/* Message bubble */}
        <div className={isUser ? 'message-user' : 'message-ai'}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* AI message actions */}
        {!isUser && (
          <div className="mt-2 flex items-center gap-2">
            {/* Copy button */}
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
              title="Copy"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>

            {/* Feedback buttons */}
            <button
              onClick={() => handleFeedback('up')}
              className={`p-1.5 rounded-lg hover:bg-white/5 transition-colors ${
                feedback === 'up' ? 'text-green-400' : 'text-gray-500 hover:text-gray-300'
              }`}
              title="Good answer"
            >
              <ThumbsUp size={14} />
            </button>
            <button
              onClick={() => handleFeedback('down')}
              className={`p-1.5 rounded-lg hover:bg-white/5 transition-colors ${
                feedback === 'down' ? 'text-red-400' : 'text-gray-500 hover:text-gray-300'
              }`}
              title="Poor answer"
            >
              <ThumbsDown size={14} />
            </button>

            {/* Sources toggle */}
            {message.sources && message.sources.length > 0 && (
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1 ml-2 px-2 py-1 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors text-xs"
              >
                <FileText size={12} />
                {message.sources.length} sources
                {showSources ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
            )}
          </div>
        )}

        {/* Sources panel */}
        {!isUser && showSources && message.sources && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 space-y-2"
          >
            {message.sources.map((source, index) => (
              <SourceCard key={index} source={source} index={index + 1} />
            ))}
          </motion.div>
        )}

        {/* Timestamp */}
        <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </motion.div>
  )
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="glass p-3 text-sm">
      <div className="flex items-start gap-2">
        <span className="flex-shrink-0 w-5 h-5 rounded bg-primary/20 text-primary text-xs flex items-center justify-center font-medium">
          {index}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-gray-300">Page {source.page_number}</span>
            <span className="px-1.5 py-0.5 rounded bg-white/5 text-gray-400 text-xs capitalize">
              {source.chunk_type}
            </span>
            {source.section_header && (
              <span className="text-gray-500 text-xs truncate">
                • {source.section_header}
              </span>
            )}
          </div>
          <p className="text-gray-400 text-xs">
            {expanded ? source.content_preview : source.content_preview.slice(0, 100) + '...'}
          </p>
          {source.content_preview.length > 100 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-primary text-xs mt-1 hover:underline"
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
