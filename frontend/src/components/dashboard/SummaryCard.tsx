import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, TrendingUp, TrendingDown, AlertTriangle, 
  Sparkles, ArrowUp, ArrowDown, Minus, ChevronDown, ChevronUp,
  BarChart3, Shield, Target, Loader2
} from 'lucide-react'
import { api } from '../../lib/api'

interface DocumentSummary {
  document_id: string
  title: string
  executive_summary: string
  key_takeaways: string[]
  financial_highlights: string[]
  risk_factors: string[]
  bull_case: string
  bear_case: string
  sentiment: 'positive' | 'neutral' | 'negative'
}

interface SummaryCardProps {
  documentId: string
}

export default function SummaryCard({ documentId }: SummaryCardProps) {
  const [summary, setSummary] = useState<DocumentSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(true)

  const fetchSummary = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/api/documents/${documentId}/summary`)
      setSummary(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail?.error || 'Failed to generate summary')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
  }, [documentId])

  const sentimentConfig = {
    positive: { icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20', label: 'Positive' },
    neutral: { icon: Minus, color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20', label: 'Neutral' },
    negative: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/20', label: 'Negative' }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="glass p-8 text-center">
          <Loader2 className="animate-spin mx-auto text-primary mb-3" size={32} />
          <p className="text-gray-400 text-sm">Generating AI summary...</p>
          <p className="text-gray-500 text-xs mt-1">Analyzing document content</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="glass p-6 border border-red-500/20">
          <p className="text-red-400 text-sm">{error}</p>
          <button onClick={fetchSummary} className="text-primary text-sm mt-2 hover:underline">
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!summary) return null

  const sentiment = sentimentConfig[summary.sentiment] || sentimentConfig.neutral
  const SentimentIcon = sentiment.icon

  return (
    <div className="p-4 space-y-4">
      {/* Header with sentiment */}
      <div className="flex items-center justify-between">
        <button 
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-white font-medium hover:text-primary transition-colors"
        >
          <Sparkles size={18} className="text-primary" />
          AI Summary
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${sentiment.bg} ${sentiment.color} border ${sentiment.border}`}>
          <SentimentIcon size={12} />
          {sentiment.label}
        </span>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-4 overflow-hidden"
          >
            {/* Executive Summary */}
            <div className="glass p-4">
              <h4 className="text-sm font-medium text-gray-300 mb-2">{summary.title}</h4>
              <p className="text-gray-400 text-sm leading-relaxed">{summary.executive_summary}</p>
            </div>

            {/* Key Takeaways */}
            <div className="glass p-4">
              <h4 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                <Target size={14} className="text-primary" />
                Key Takeaways
              </h4>
              <ul className="space-y-2">
                {summary.key_takeaways.map((takeaway, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-2 text-sm text-gray-400"
                  >
                    <span className="w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5 font-medium">
                      {i + 1}
                    </span>
                    {takeaway}
                  </motion.li>
                ))}
              </ul>
            </div>

            {/* Financial Highlights */}
            {summary.financial_highlights.length > 0 && (
              <div className="glass p-4">
                <h4 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                  <BarChart3 size={14} className="text-emerald-400" />
                  Financial Highlights
                </h4>
                <ul className="space-y-2">
                  {summary.financial_highlights.map((highlight, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                      <ArrowUp size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                      {highlight}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risk Factors */}
            {summary.risk_factors.length > 0 && (
              <div className="glass p-4">
                <h4 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                  <AlertTriangle size={14} className="text-amber-400" />
                  Risk Factors
                </h4>
                <ul className="space-y-2">
                  {summary.risk_factors.map((risk, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                      <Shield size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Bull/Bear Case */}
            <div className="grid grid-cols-2 gap-3">
              <div className="glass p-3 border border-emerald-500/10">
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingUp size={14} className="text-emerald-400" />
                  <span className="text-xs font-medium text-emerald-400">Bull Case</span>
                </div>
                <p className="text-gray-400 text-xs leading-relaxed">{summary.bull_case}</p>
              </div>
              <div className="glass p-3 border border-red-500/10">
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingDown size={14} className="text-red-400" />
                  <span className="text-xs font-medium text-red-400">Bear Case</span>
                </div>
                <p className="text-gray-400 text-xs leading-relaxed">{summary.bear_case}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
