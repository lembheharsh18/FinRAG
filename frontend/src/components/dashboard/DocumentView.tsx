import { motion } from 'framer-motion'
import { FileText, Calendar, Layers } from 'lucide-react'
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

export default function DocumentView({ document }: DocumentViewProps) {
  return (
    <div className="h-full flex">
      {/* Document info panel (40%) */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-2/5 border-r border-white/5 p-6 overflow-y-auto"
      >
        {/* Document header */}
        <div className="flex items-start gap-4 mb-6">
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
        <div className="glass p-4 space-y-4 mb-6">
          <div className="flex items-center gap-3">
            <Calendar className="text-gray-400" size={18} />
            <div>
              <p className="text-sm text-gray-400">Uploaded</p>
              <p className="text-white">
                {document.uploadedAt.toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Layers className="text-gray-400" size={18} />
            <div>
              <p className="text-sm text-gray-400">Chunks indexed</p>
              <p className="text-white">{document.chunks || 'Processing...'}</p>
            </div>
          </div>
        </div>

        {/* Placeholder for PDF preview */}
        <div className="glass p-4">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Document Preview</h3>
          <div className="aspect-[3/4] bg-dark-500 rounded-lg flex items-center justify-center">
            <div className="text-center text-gray-500">
              <FileText size={48} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">PDF preview coming soon</p>
            </div>
          </div>
        </div>

        {/* Example questions */}
        <div className="mt-6">
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
