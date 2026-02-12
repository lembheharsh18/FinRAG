import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, GitCompare, Loader2, 
  FileText, ChevronRight, Sparkles
} from 'lucide-react'
import { api } from '../lib/api'

interface Document {
  document_id: string
  filename: string
  chunk_count: number
}

interface ComparisonEntry {
  document: string
  value: string
}

interface ComparisonDimension {
  dimension: string
  entries: ComparisonEntry[]
  insight: string
}

interface CompareResult {
  comparison_summary: string
  dimensions: ComparisonDimension[]
  overall_insight: string
  documents_compared: string[]
}

export default function ComparePage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [result, setResult] = useState<CompareResult | null>(null)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/collections/stats')
      setDocuments(response.data.documents || [])
    } catch (err) {
      console.error('Failed to load documents')
    } finally {
      setLoadingDocs(false)
    }
  }

  const toggleDoc = (docId: string) => {
    setSelectedDocs(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : prev.length < 5 ? [...prev, docId] : prev
    )
  }

  const handleCompare = async () => {
    if (selectedDocs.length < 2) return
    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/api/compare', {
        document_ids: selectedDocs,
        question: question || undefined
      })
      setResult(response.data)
    } catch (err: any) {
      console.error('Comparison failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button 
            onClick={() => navigate('/dashboard')}
            className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <GitCompare className="text-primary" size={28} />
              Document Comparison
            </h1>
            <p className="text-gray-400 text-sm mt-1">Compare financial documents side by side</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Document Selection */}
          <div className="glass p-6">
            <h3 className="text-white font-medium mb-4">Select Documents (2-5)</h3>
            
            {loadingDocs ? (
              <div className="text-center py-8">
                <Loader2 className="animate-spin mx-auto text-primary" size={24} />
              </div>
            ) : documents.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">No documents uploaded yet</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {documents.map(doc => (
                  <button
                    key={doc.document_id}
                    onClick={() => toggleDoc(doc.document_id)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all text-sm ${
                      selectedDocs.includes(doc.document_id)
                        ? 'bg-primary/10 text-primary border border-primary/20'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <FileText size={16} className="flex-shrink-0" />
                    <span className="truncate flex-1">{doc.filename || doc.document_id}</span>
                    {selectedDocs.includes(doc.document_id) && (
                      <span className="w-5 h-5 rounded-full bg-primary text-white text-xs flex items-center justify-center">
                        {selectedDocs.indexOf(doc.document_id) + 1}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Optional question */}
            <div className="mt-4">
              <label className="text-xs text-gray-400 mb-1 block">Comparison Focus (optional)</label>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g., Compare revenue growth"
                className="input-field w-full text-sm"
              />
            </div>

            <button
              onClick={handleCompare}
              disabled={selectedDocs.length < 2 || loading}
              className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <GitCompare size={16} />
                  Compare ({selectedDocs.length} docs)
                </>
              )}
            </button>
          </div>

          {/* Results */}
          <div className="col-span-2">
            {!result && !loading && (
              <div className="glass p-12 text-center">
                <GitCompare className="mx-auto text-gray-600 mb-4" size={48} />
                <p className="text-gray-400 mb-2">Select at least 2 documents to compare</p>
                <p className="text-gray-500 text-sm">The AI will analyze and generate a side-by-side comparison</p>
              </div>
            )}

            {loading && (
              <div className="glass p-12 text-center">
                <Loader2 className="animate-spin mx-auto text-primary mb-4" size={40} />
                <p className="text-gray-400">Analyzing documents...</p>
                <p className="text-gray-500 text-sm mt-1">Comparing across {selectedDocs.length} documents</p>
              </div>
            )}

            {result && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Summary */}
                <div className="glass p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles size={16} className="text-primary" />
                    <h3 className="text-white font-medium">Comparison Summary</h3>
                  </div>
                  <p className="text-gray-400 text-sm leading-relaxed">{result.comparison_summary}</p>
                </div>

                {/* Comparison Table */}
                {result.dimensions.map((dim, i) => (
                  <motion.div
                    key={dim.dimension}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="glass p-5"
                  >
                    <h4 className="text-white font-medium text-sm mb-3">{dim.dimension}</h4>
                    <div className="space-y-2 mb-3">
                      {dim.entries.map((entry, j) => (
                        <div key={j} className="flex items-start gap-3 text-sm">
                          <span className="w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                            {j + 1}
                          </span>
                          <div>
                            <span className="text-gray-300 font-medium">{entry.document}:</span>
                            <span className="text-gray-400 ml-1">{entry.value}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="flex items-start gap-2 bg-primary/5 rounded-lg p-2.5">
                      <ChevronRight size={14} className="text-primary mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-gray-400">{dim.insight}</p>
                    </div>
                  </motion.div>
                ))}

                {/* Overall Insight */}
                <div className="glass p-5 border border-primary/10">
                  <h4 className="text-primary font-medium text-sm mb-2">Key Takeaway</h4>
                  <p className="text-gray-300 text-sm">{result.overall_insight}</p>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
