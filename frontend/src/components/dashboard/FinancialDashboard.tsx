import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  DollarSign, TrendingUp, TrendingDown, BarChart3, 
  PieChart, Loader2, RefreshCw, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import { api } from '../../lib/api'

interface FinancialMetric {
  name: string
  value: string
  change?: string
  category: string
}

interface KeyRatio {
  name: string
  value: string
}

interface FinancialsData {
  document_id: string
  company_name: string
  period: string
  metrics: FinancialMetric[]
  key_ratios: KeyRatio[]
}

interface FinancialDashboardProps {
  documentId: string
}

const categoryConfig: Record<string, { icon: any; color: string; bg: string }> = {
  income: { icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
  per_share: { icon: BarChart3, color: 'text-blue-400', bg: 'bg-blue-400/10' },
  margin: { icon: PieChart, color: 'text-purple-400', bg: 'bg-purple-400/10' },
  balance_sheet: { icon: TrendingUp, color: 'text-amber-400', bg: 'bg-amber-400/10' },
  other: { icon: BarChart3, color: 'text-gray-400', bg: 'bg-gray-400/10' }
}

export default function FinancialDashboard({ documentId }: FinancialDashboardProps) {
  const [data, setData] = useState<FinancialsData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchFinancials = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/api/documents/${documentId}/financials`)
      setData(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail?.error || 'Failed to extract financials')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFinancials()
  }, [documentId])

  if (loading) {
    return (
      <div className="p-6">
        <div className="glass p-8 text-center">
          <Loader2 className="animate-spin mx-auto text-primary mb-3" size={32} />
          <p className="text-gray-400 text-sm">Extracting financial metrics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="glass p-6 border border-red-500/20">
          <p className="text-red-400 text-sm">{error}</p>
          <button onClick={fetchFinancials} className="text-primary text-sm mt-2 hover:underline">
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const isPositiveChange = (change?: string) => {
    if (!change) return null
    return change.startsWith('+') || (!change.startsWith('-') && parseFloat(change) > 0)
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-white font-medium flex items-center gap-2">
            <BarChart3 size={18} className="text-primary" />
            Financial Metrics
          </h3>
          <p className="text-gray-500 text-xs mt-0.5">
            {data.company_name} · {data.period}
          </p>
        </div>
        <button 
          onClick={fetchFinancials}
          className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
          title="Refresh"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        {data.metrics.map((metric, i) => {
          const config = categoryConfig[metric.category] || categoryConfig.other
          const Icon = config.icon
          const positive = isPositiveChange(metric.change)

          return (
            <motion.div
              key={metric.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass p-3 hover:bg-white/[0.04] transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-7 h-7 rounded-lg ${config.bg} flex items-center justify-center`}>
                  <Icon size={14} className={config.color} />
                </div>
                <span className="text-xs text-gray-400 truncate">{metric.name}</span>
              </div>
              <div className="flex items-end justify-between">
                <span className="text-lg font-semibold text-white">{metric.value}</span>
                {metric.change && (
                  <span className={`flex items-center gap-0.5 text-xs font-medium ${
                    positive ? 'text-emerald-400' : positive === false ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {positive ? <ArrowUpRight size={12} /> : positive === false ? <ArrowDownRight size={12} /> : null}
                    {metric.change}
                  </span>
                )}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Key Ratios */}
      {data.key_ratios.length > 0 && (
        <div className="glass p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
            <PieChart size={14} className="text-purple-400" />
            Key Ratios
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {data.key_ratios.map((ratio, i) => (
              <motion.div
                key={ratio.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 + i * 0.05 }}
                className="text-center"
              >
                <p className="text-lg font-semibold text-white">{ratio.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{ratio.name}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
