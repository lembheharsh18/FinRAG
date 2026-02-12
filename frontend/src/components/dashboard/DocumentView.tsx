import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Calendar, Layers, Eye, MessageSquare } from 'lucide-react'
import ChatContainer from '../chat/ChatContainer'

interface Document {
  id: string
  name: string
  uploadedAt: Date
  pageCount: number
  chunks?: number
}

interface DocumentViewProps {
  document: Document
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function DocumentView({ document }: DocumentViewProps) {
  const [activeTab, setActiveTab] = useState<'preview' | 'chat'>('chat')

  // Build the PDF preview URL (auth token will be needed for the request)
  const pdfUrl = `${API_URL}/api/documents/${document.id}/file`

  return (
    <div className="h-full flex">
      {/* Document info panel (40%) */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-2/5 border-r border-white/5 flex flex-col overflow-hidden"
      >
        {/* Document header */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-start gap-4 mb-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-primary/20 flex items-center justify-center flex-shrink-0">
              <FileText className="text-primary" size={28} />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-semibold text-white truncate">
                {document.name}
              </h1>
              <p className="text-gray-400 text-sm mt-1">
                PDF Document
              </p>
            </div>
          </div>

          {/* Document stats */}
          <div className="glass p-3 space-y-3">
            <div className="flex items-center gap-3">
              <Calendar className="text-gray-400" size={16} />
              <div>
                <p className="text-xs text-gray-400">Uploaded</p>
                <p className="text-white text-sm">
                  {document.uploadedAt.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Layers className="text-gray-400" size={16} />
              <div>
                <p className="text-xs text-gray-400">Chunks indexed</p>
                <p className="text-white text-sm">{document.chunks || 'Processing...'}</p>
              </div>
            </div>
          </div>

          {/* Tab toggle */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'preview' 
                  ? 'bg-primary/20 text-primary border border-primary/30' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Eye size={16} />
              Preview
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'chat' 
                  ? 'bg-primary/20 text-primary border border-primary/30' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <MessageSquare size={16} />
              Chat
            </button>
          </div>
        </div>

        {/* Content area based on tab */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'preview' ? (
            <div className="h-full p-4">
              <div className="h-full rounded-lg overflow-hidden border border-white/10 bg-white">
                <iframe
                  src={pdfUrl}
                  className="w-full h-full"
                  title={`Preview of ${document.name}`}
                />
              </div>
            </div>
          ) : (
            <div className="p-4 overflow-y-auto h-full">
              {/* Example questions */}
              <h3 className="text-sm font-medium text-gray-300 mb-3">Try asking</h3>
              <div className="space-y-2">
                {[
                  "What was the total revenue?",
                  "Summarize the key findings",
                  "What are the main risks mentioned?"
                ].map((question, i) => (
                  <div 
                    key={i}
                    className="glass-hover p-3 text-sm text-gray-300 cursor-pointer"
                  >
                    "{question}"
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Chat interface (60%) */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex-1"
      >
        <ChatContainer documentId={document.id} documentName={document.name} />
      </motion.div>
    </div>
  )
}
