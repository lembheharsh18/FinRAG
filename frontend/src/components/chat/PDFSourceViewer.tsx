import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, ChevronLeft, ChevronRight, Search, 
  Maximize2, Minimize2, Highlighter, Eye
} from 'lucide-react'

interface Source {
  document_id: string
  content_preview: string
  page_number?: number
  chunk_type?: string
  section_header?: string
  relevance_score?: number
}

interface PDFSourceViewerProps {
  documentId: string
  documentName: string
  sources: Source[]
  apiBaseUrl: string
}

export default function PDFSourceViewer({ documentId, sources, apiBaseUrl }: PDFSourceViewerProps) {
  const [activeSource, setActiveSource] = useState<number>(0)
  const [expanded, setExpanded] = useState(false)
  const [searchText, setSearchText] = useState('')

  const currentSource = sources[activeSource]

  const getRelevanceColor = (score?: number) => {
    if (!score) return 'text-gray-400'
    if (score >= 0.8) return 'text-emerald-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-orange-400'
  }

  const getRelevanceLabel = (score?: number) => {
    if (!score) return 'Unknown'
    if (score >= 0.8) return 'High'
    if (score >= 0.6) return 'Medium'
    return 'Low'
  }

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
    return parts.map((part) =>
      part.toLowerCase() === query.toLowerCase()
        ? `<mark class="bg-yellow-400/30 text-yellow-200 px-0.5 rounded">${part}</mark>`
        : part
    ).join('')
  }

  if (sources.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass border border-white/10 rounded-xl overflow-hidden transition-all duration-300 ${
        expanded ? 'fixed inset-8 z-50' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
        <div className="flex items-center gap-3">
          <Highlighter size={16} className="text-primary" />
          <span className="text-white font-medium text-sm">Source Viewer</span>
          <span className="text-xs text-gray-500">
            {sources.length} source{sources.length > 1 ? 's' : ''} found
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Highlight text..."
              className="bg-white/5 border border-white/10 rounded-lg pl-7 pr-3 py-1 text-xs text-white placeholder-gray-500 w-36 focus:outline-none focus:border-primary/50"
            />
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          >
            {expanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {/* Source Tabs */}
      <div className="flex gap-1 px-3 pt-3 overflow-x-auto scrollbar-thin">
        {sources.map((src, i) => (
          <button
            key={i}
            onClick={() => setActiveSource(i)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg text-xs font-medium whitespace-nowrap transition-all ${
              i === activeSource
                ? 'bg-white/10 text-white border-b-2 border-primary'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <FileText size={12} />
            {src.section_header || `Source ${i + 1}`}
            <span className={`text-[10px] ${getRelevanceColor(src.relevance_score)}`}>
              {getRelevanceLabel(src.relevance_score)}
            </span>
          </button>
        ))}
      </div>

      {/* Source Content */}
      <div className={`${expanded ? 'h-[calc(100%-120px)]' : 'max-h-80'} overflow-y-auto`}>
        <AnimatePresence mode="wait">
          {currentSource && (
            <motion.div
              key={activeSource}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-4"
            >
              {/* Source Metadata */}
              <div className="flex items-center gap-4 mb-3">
                {currentSource.page_number && (
                  <span className="bg-primary/10 text-primary text-xs px-2 py-0.5 rounded-full">
                    Page {currentSource.page_number}
                  </span>
                )}
                {currentSource.chunk_type && (
                  <span className="bg-white/5 text-gray-400 text-xs px-2 py-0.5 rounded-full">
                    {currentSource.chunk_type}
                  </span>
                )}
                {currentSource.relevance_score && (
                  <span className={`text-xs ${getRelevanceColor(currentSource.relevance_score)}`}>
                    {(currentSource.relevance_score * 100).toFixed(0)}% match
                  </span>
                )}
              </div>

              {/* Section Header */}
              {currentSource.section_header && (
                <h4 className="text-white font-medium text-sm mb-2">
                  § {currentSource.section_header}
                </h4>
              )}

              {/* Highlighted Content */}
              <div
                className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-mono bg-white/3 rounded-lg p-4 border border-white/5"
                dangerouslySetInnerHTML={{
                  __html: highlightText(currentSource.content_preview, searchText)
                }}
              />

              {/* PDF Preview Link */}
              <div className="mt-3 flex items-center gap-2">
                <a
                  href={`${apiBaseUrl}/api/documents/${documentId}/file${currentSource.page_number ? `#page=${currentSource.page_number}` : ''}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  <Eye size={12} />
                  View in PDF
                  {currentSource.page_number ? ` (Page ${currentSource.page_number})` : ''}
                </a>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Footer */}
      {sources.length > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-white/10 bg-white/3">
          <button
            onClick={() => setActiveSource(Math.max(0, activeSource - 1))}
            disabled={activeSource === 0}
            className="p-1 rounded hover:bg-white/5 text-gray-400 disabled:opacity-30 transition-all"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs text-gray-500">
            {activeSource + 1} of {sources.length}
          </span>
          <button
            onClick={() => setActiveSource(Math.min(sources.length - 1, activeSource + 1))}
            disabled={activeSource === sources.length - 1}
            className="p-1 rounded hover:bg-white/5 text-gray-400 disabled:opacity-30 transition-all"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Expanded backdrop */}
      {expanded && (
        <div
          className="fixed inset-0 bg-black/60 -z-10"
          onClick={() => setExpanded(false)}
        />
      )}
    </motion.div>
  )
}
