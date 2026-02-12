import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  BarChart3, FileText, MessageSquare, Zap, Clock, 
  TrendingUp, Hash, ArrowLeft, Loader2, Activity
} from 'lucide-react'
import { api } from '../lib/api'

interface AnalyticsData {
  total_queries: number
  total_documents: number
  total_tokens_used: number
  avg_confidence: number
  avg_response_time: number
  queries_by_day: Record<string, number>
  popular_topics: { topic: string; count: number }[]
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/analytics')
      setData(response.data)
    } catch (err) {
      console.error('Failed to fetch analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto text-primary mb-3" size={40} />
          <p className="text-gray-400">Loading analytics...</p>
        </div>
      </div>
    )
  }

  const stats = [
    { label: 'Total Queries', value: data?.total_queries || 0, icon: MessageSquare, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'Documents Indexed', value: data?.total_documents || 0, icon: FileText, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
    { label: 'Tokens Used', value: (data?.total_tokens_used || 0).toLocaleString(), icon: Zap, color: 'text-amber-400', bg: 'bg-amber-400/10' },
    { label: 'Avg Confidence', value: `${((data?.avg_confidence || 0) * 100).toFixed(1)}%`, icon: TrendingUp, color: 'text-purple-400', bg: 'bg-purple-400/10' },
  ]

  const queryDays = Object.entries(data?.queries_by_day || {})
  const maxQueries = Math.max(...queryDays.map(([, v]) => v), 1)

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
              <Activity className="text-primary" size={28} />
              RAG Analytics
            </h1>
            <p className="text-gray-400 text-sm mt-1">Usage statistics and performance metrics</p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass p-6"
            >
              <div className={`w-12 h-12 rounded-xl ${stat.bg} flex items-center justify-center mb-4`}>
                <stat.icon size={24} className={stat.color} />
              </div>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
              <p className="text-sm text-gray-400 mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Queries by Day Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass p-6"
          >
            <h3 className="text-white font-medium mb-4 flex items-center gap-2">
              <Clock size={18} className="text-primary" />
              Queries by Day
            </h3>
            {queryDays.length > 0 ? (
              <div className="space-y-3">
                {queryDays.map(([day, count]) => (
                  <div key={day} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-24 flex-shrink-0">
                      {new Date(day).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                    <div className="flex-1 h-6 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(count / maxQueries) * 100}%` }}
                        transition={{ delay: 0.5, duration: 0.5 }}
                        className="h-full bg-gradient-to-r from-primary to-primary/60 rounded-full"
                      />
                    </div>
                    <span className="text-sm text-white font-medium w-8 text-right">{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm text-center py-8">No query data yet. Start asking questions!</p>
            )}
          </motion.div>

          {/* Popular Topics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass p-6"
          >
            <h3 className="text-white font-medium mb-4 flex items-center gap-2">
              <Hash size={18} className="text-primary" />
              Popular Topics
            </h3>
            {(data?.popular_topics || []).length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {data?.popular_topics.map((topic, i) => (
                  <motion.span
                    key={topic.topic}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 + i * 0.05 }}
                    className="px-3 py-1.5 rounded-full text-sm font-medium"
                    style={{
                      background: `rgba(99, 102, 241, ${0.1 + (topic.count / 10) * 0.2})`,
                      color: `rgba(165, 180, 252, ${0.6 + (topic.count / 10) * 0.4})`
                    }}
                  >
                    {topic.topic}
                    <span className="ml-1.5 text-xs opacity-60">({topic.count})</span>
                  </motion.span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm text-center py-8">No topics tracked yet</p>
            )}
          </motion.div>
        </div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass p-6 mt-6"
        >
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <BarChart3 size={18} className="text-primary" />
            Performance Summary
          </h3>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-white">
                {data?.avg_response_time ? `${data.avg_response_time.toFixed(1)}s` : 'N/A'}
              </p>
              <p className="text-sm text-gray-400 mt-1">Avg Response Time</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">
                {((data?.avg_confidence || 0) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-400 mt-1">Avg Retrieval Confidence</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">
                {data?.total_queries && data?.total_tokens_used 
                  ? Math.round(data.total_tokens_used / data.total_queries)
                  : 'N/A'}
              </p>
              <p className="text-sm text-gray-400 mt-1">Avg Tokens per Query</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
