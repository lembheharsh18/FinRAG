import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, Loader2, Scale, Zap, Shield, Clock,
  Trophy, BarChart3, Send,
  FileText, AlertTriangle, Sparkles
} from 'lucide-react'
import { api } from '../lib/api'

interface EvalSource {
  page_number: number
  chunk_type: string
  section_header?: string
  content_preview: string
}

interface EvalResult {
  question: string
  rag_answer: string
  rag_sources: EvalSource[]
  rag_faithfulness: number
  rag_reasoning: string
  llm_answer: string
  llm_faithfulness: number
  llm_reasoning: string
  rag_response_time: number
  llm_response_time: number
  winner: string
  timestamp: string
}

interface EvalReport {
  total_evaluations: number
  avg_rag_faithfulness: number
  avg_llm_faithfulness: number
  rag_win_rate: number
  avg_rag_response_time: number
  avg_llm_response_time: number
}

// Circular progress gauge
function FaithfulnessGauge({ score, label, color }: { score: number, label: string, color: string }) {
  const percentage = Math.round(score * 100)
  const circumference = 2 * Math.PI * 40
  const offset = circumference - (score * circumference)

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
          <motion.circle
            cx="50" cy="50" r="40" fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-white">{percentage}%</span>
        </div>
      </div>
      <span className="text-xs text-gray-400 mt-2">{label}</span>
    </div>
  )
}

export default function EvaluationPage() {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [documentId, setDocumentId] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<EvalResult | null>(null)
  const [report, setReport] = useState<EvalReport | null>(null)
  const [reportLoading, setReportLoading] = useState(true)

  useEffect(() => {
    fetchReport()
  }, [])

  const fetchReport = async () => {
    try {
      const resp = await api.get('/api/evaluate/report')
      setReport(resp.data)
    } catch {
      // No evaluations yet
    } finally {
      setReportLoading(false)
    }
  }

  const runEvaluation = async () => {
    if (!question.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const resp = await api.post('/api/evaluate/compare', {
        question: question.trim(),
        document_id: documentId || undefined,
        n_chunks: 5
      })
      setResult(resp.data)
      fetchReport() // Refresh stats
    } catch (err: any) {
      console.error('Evaluation failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark">
      {/* Header */}
      <div className="border-b border-white/5 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="p-2 glass-hover rounded-lg">
            <ArrowLeft size={18} className="text-gray-400" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Scale size={22} className="text-primary" />
              RAG vs LLM Evaluation
            </h1>
            <p className="text-sm text-gray-400">Compare RAG-grounded answers with LLM-only answers</p>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Aggregate Stats */}
        {!reportLoading && report && report.total_evaluations > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 md:grid-cols-5 gap-4"
          >
            {[
              { icon: BarChart3, label: 'Evaluations', value: report.total_evaluations.toString(), color: 'text-primary' },
              { icon: Shield, label: 'RAG Faithfulness', value: `${Math.round(report.avg_rag_faithfulness * 100)}%`, color: 'text-green-400' },
              { icon: AlertTriangle, label: 'LLM Faithfulness', value: `${Math.round(report.avg_llm_faithfulness * 100)}%`, color: 'text-yellow-400' },
              { icon: Trophy, label: 'RAG Win Rate', value: `${Math.round(report.rag_win_rate * 100)}%`, color: 'text-emerald-400' },
              { icon: Clock, label: 'Avg RAG Time', value: `${report.avg_rag_response_time}s`, color: 'text-blue-400' },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass p-4 rounded-xl text-center"
              >
                <stat.icon size={18} className={`mx-auto mb-2 ${stat.color}`} />
                <p className="text-lg font-bold text-white">{stat.value}</p>
                <p className="text-xs text-gray-400">{stat.label}</p>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass p-6 rounded-2xl"
        >
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Sparkles size={18} className="text-primary" />
            Run New Comparison
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Question</label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && runEvaluation()}
                  placeholder="e.g., What was the company's revenue growth last year?"
                  className="input-field flex-1"
                  disabled={loading}
                />
                <button
                  onClick={runEvaluation}
                  disabled={loading || !question.trim()}
                  className="btn-primary flex items-center gap-2 !px-6"
                >
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                  {loading ? 'Evaluating...' : 'Compare'}
                </button>
              </div>
            </div>

            <div>
              <label className="text-sm text-gray-400 mb-1 block">Document ID (optional)</label>
              <input
                type="text"
                value={documentId}
                onChange={(e) => setDocumentId(e.target.value)}
                placeholder="Leave empty to search across all documents"
                className="input-field"
                disabled={loading}
              />
            </div>
          </div>

          {/* Sample questions */}
          <div className="mt-4 flex flex-wrap gap-2">
            {[
              "What is the company's net profit margin?",
              "What are the main risk factors?",
              "How did revenue change year-over-year?",
            ].map(q => (
              <button
                key={q}
                onClick={() => setQuestion(q)}
                className="text-xs glass px-3 py-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Loading State */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass p-12 rounded-2xl text-center"
          >
            <Loader2 size={40} className="animate-spin text-primary mx-auto mb-4" />
            <p className="text-white font-medium">Running evaluation...</p>
            <p className="text-sm text-gray-400 mt-1">Generating RAG + LLM answers and scoring faithfulness</p>
          </motion.div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Winner banner */}
              <div className={`glass p-4 rounded-xl border ${
                result.winner === 'rag' ? 'border-green-500/30 bg-green-500/5' : 'border-yellow-500/30 bg-yellow-500/5'
              }`}>
                <div className="flex items-center gap-3">
                  <Trophy size={20} className={result.winner === 'rag' ? 'text-green-400' : 'text-yellow-400'} />
                  <div>
                    <p className="text-white font-medium">
                      {result.winner === 'rag' ? '🏆 RAG Wins!' : '⚠️ LLM won this round'}
                    </p>
                    <p className="text-xs text-gray-400">
                      RAG faithfulness: {Math.round(result.rag_faithfulness * 100)}% vs LLM: {Math.round(result.llm_faithfulness * 100)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Gauges */}
              <div className="glass p-6 rounded-2xl flex items-center justify-center gap-12">
                <FaithfulnessGauge score={result.rag_faithfulness} label="RAG Faithfulness" color="#22c55e" />
                <div className="text-gray-500 text-2xl font-bold">VS</div>
                <FaithfulnessGauge score={result.llm_faithfulness} label="LLM Faithfulness" color="#eab308" />
              </div>

              {/* Side-by-side answers */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* RAG Answer */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="glass p-6 rounded-2xl border border-green-500/10"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <Shield size={18} className="text-green-400" />
                    <h4 className="text-white font-semibold">RAG Answer</h4>
                    <span className="ml-auto text-xs glass px-2 py-1 rounded text-green-400 flex items-center gap-1">
                      <Clock size={10} /> {result.rag_response_time}s
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{result.rag_answer}</p>
                  
                  {/* Sources */}
                  {result.rag_sources.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <p className="text-xs text-gray-500 font-medium">Sources:</p>
                      {result.rag_sources.map((src, i) => (
                        <div key={i} className="glass p-2 rounded-lg text-xs">
                          <div className="flex items-center gap-2 text-gray-400">
                            <FileText size={10} />
                            <span>Page {src.page_number} • {src.chunk_type}</span>
                            {src.section_header && <span>• {src.section_header}</span>}
                          </div>
                          <p className="text-gray-500 mt-1 line-clamp-2">{src.content_preview}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reasoning */}
                  <div className="mt-4 p-3 bg-green-500/5 rounded-lg border border-green-500/10">
                    <p className="text-xs text-green-400 font-medium mb-1">Judge Reasoning:</p>
                    <p className="text-xs text-gray-400">{result.rag_reasoning}</p>
                  </div>
                </motion.div>

                {/* LLM Answer */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="glass p-6 rounded-2xl border border-yellow-500/10"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <Zap size={18} className="text-yellow-400" />
                    <h4 className="text-white font-semibold">LLM-Only Answer</h4>
                    <span className="ml-auto text-xs glass px-2 py-1 rounded text-yellow-400 flex items-center gap-1">
                      <Clock size={10} /> {result.llm_response_time}s
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{result.llm_answer}</p>

                  <div className="mt-4 p-3 bg-yellow-500/5 rounded-lg border border-yellow-500/10">
                    <p className="text-xs text-yellow-400 font-medium mb-1">Judge Reasoning:</p>
                    <p className="text-xs text-gray-400">{result.llm_reasoning}</p>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
