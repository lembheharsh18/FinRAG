import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  Bell, Plus, Trash2, TrendingUp, TrendingDown,
  ArrowLeft, Loader2, CheckCircle, RefreshCw, Search,
  DollarSign, Activity
} from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../lib/api'

interface Alert {
  id: string
  ticker: string
  condition: string
  target_price: number
  current_price?: number
  created_at: string
  triggered: boolean
  triggered_at?: string
  document_id?: string
  note?: string
}

interface ExtractedTicker {
  symbol: string
  company: string
  context: string
}

export default function AlertsPage() {
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [tickers, setTickers] = useState<ExtractedTicker[]>([])
  const [loadingTickers, setLoadingTickers] = useState(false)
  const [docId, setDocId] = useState('')

  // Form state
  const [ticker, setTicker] = useState('')
  const [condition, setCondition] = useState<'above' | 'below'>('above')
  const [targetPrice, setTargetPrice] = useState('')
  const [note, setNote] = useState('')

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    try {
      const response = await api.get('/api/alerts')
      setAlerts(response.data.alerts || [])
    } catch (err) {
      console.error('Failed to fetch alerts')
    } finally {
      setLoading(false)
    }
  }

  const createAlert = async () => {
    if (!ticker || !targetPrice) return
    try {
      const response = await api.post('/api/alerts', {
        ticker: ticker.toUpperCase(),
        condition,
        target_price: parseFloat(targetPrice),
        note: note || undefined
      })
      setAlerts(prev => [...prev, response.data])
      setShowCreate(false)
      setTicker('')
      setTargetPrice('')
      setNote('')
      toast.success(`Alert created for ${ticker.toUpperCase()}`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail?.error || 'Failed to create alert')
    }
  }

  const deleteAlert = async (alertId: string) => {
    try {
      await api.delete(`/api/alerts/${alertId}`)
      setAlerts(prev => prev.filter(a => a.id !== alertId))
      toast.success('Alert deleted')
    } catch {
      toast.error('Failed to delete alert')
    }
  }

  const checkAlerts = async () => {
    setChecking(true)
    try {
      const response = await api.post('/api/alerts/check')
      const triggered = response.data.triggered || []

      if (triggered.length > 0) {
        triggered.forEach((t: any) => {
          toast.success(`🔔 ${t.ticker} hit $${t.current_price} (target: $${t.target_price})`, {
            duration: 5000
          })
        })
      } else {
        toast.success('All alerts checked — none triggered')
      }

      // Refresh alerts to get updated prices
      await fetchAlerts()
    } catch (err) {
      toast.error('Failed to check alerts')
    } finally {
      setChecking(false)
    }
  }

  const extractTickers = async () => {
    if (!docId) return
    setLoadingTickers(true)
    try {
      const response = await api.get(`/api/documents/${docId}/tickers`)
      setTickers(response.data.tickers || [])
    } catch {
      toast.error('Failed to extract tickers')
    } finally {
      setLoadingTickers(false)
    }
  }

  const selectTicker = (symbol: string) => {
    setTicker(symbol)
    setShowCreate(true)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <Loader2 className="animate-spin text-primary" size={40} />
      </div>
    )
  }

  const activeAlerts = alerts.filter(a => !a.triggered)
  const triggeredAlerts = alerts.filter(a => a.triggered)

  return (
    <div className="min-h-screen bg-dark p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/dashboard')}
              className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <Bell className="text-primary" size={28} />
                Financial Alerts
              </h1>
              <p className="text-gray-400 text-sm mt-1">Set price alerts for stocks mentioned in your documents</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={checkAlerts}
              disabled={checking || alerts.length === 0}
              className="btn-secondary flex items-center gap-2 py-2 px-4 text-sm disabled:opacity-50"
            >
              {checking ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Check Now
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="btn-primary flex items-center gap-2 py-2 px-4 text-sm"
            >
              <Plus size={14} />
              New Alert
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Alerts List */}
          <div className="col-span-2 space-y-4">
            {/* Active Alerts */}
            <div>
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Activity size={16} className="text-primary" />
                Active Alerts ({activeAlerts.length})
              </h3>
              {activeAlerts.length === 0 ? (
                <div className="glass p-8 text-center">
                  <Bell className="mx-auto text-gray-600 mb-3" size={32} />
                  <p className="text-gray-400 text-sm">No active alerts</p>
                  <p className="text-gray-500 text-xs mt-1">Create one to start monitoring</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {activeAlerts.map((alert, i) => (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="glass p-4 flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          alert.condition === 'above' 
                            ? 'bg-emerald-400/10' 
                            : 'bg-red-400/10'
                        }`}>
                          {alert.condition === 'above' 
                            ? <TrendingUp size={18} className="text-emerald-400" />
                            : <TrendingDown size={18} className="text-red-400" />
                          }
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-white font-semibold">{alert.ticker}</span>
                            <span className="text-xs text-gray-500">
                              {alert.condition === 'above' ? '≥' : '≤'} ${alert.target_price.toFixed(2)}
                            </span>
                          </div>
                          {alert.current_price && (
                            <p className="text-xs text-gray-400">
                              Current: ${alert.current_price.toFixed(2)}
                            </p>
                          )}
                          {alert.note && (
                            <p className="text-xs text-gray-500 mt-0.5">{alert.note}</p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => deleteAlert(alert.id)}
                        className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Triggered Alerts */}
            {triggeredAlerts.length > 0 && (
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <CheckCircle size={16} className="text-emerald-400" />
                  Triggered ({triggeredAlerts.length})
                </h3>
                <div className="space-y-2">
                  {triggeredAlerts.map(alert => (
                    <div key={alert.id} className="glass p-4 flex items-center justify-between opacity-60">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-emerald-400/10 flex items-center justify-center">
                          <CheckCircle size={18} className="text-emerald-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-white font-semibold">{alert.ticker}</span>
                            <span className="text-xs text-emerald-400">Triggered</span>
                          </div>
                          <p className="text-xs text-gray-400">
                            Hit ${alert.current_price?.toFixed(2)} (target: ${alert.target_price.toFixed(2)})
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteAlert(alert.id)}
                        className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Create Alert + Ticker Extraction */}
          <div className="space-y-4">
            {/* Create Alert Form */}
            <AnimatePresence>
              {showCreate && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="glass p-5"
                >
                  <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                    <Plus size={16} className="text-primary" />
                    Create Alert
                  </h3>

                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Ticker Symbol</label>
                      <input
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="e.g., AAPL"
                        className="input-field w-full text-sm"
                      />
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => setCondition('above')}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                          condition === 'above'
                            ? 'bg-emerald-400/20 text-emerald-400 border border-emerald-400/30'
                            : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                        }`}
                      >
                        ↑ Price Above
                      </button>
                      <button
                        onClick={() => setCondition('below')}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                          condition === 'below'
                            ? 'bg-red-400/20 text-red-400 border border-red-400/30'
                            : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                        }`}
                      >
                        ↓ Price Below
                      </button>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Target Price ($)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={targetPrice}
                        onChange={(e) => setTargetPrice(e.target.value)}
                        placeholder="150.00"
                        className="input-field w-full text-sm"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Note (optional)</label>
                      <input
                        type="text"
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="Buy signal from Q4 report"
                        className="input-field w-full text-sm"
                      />
                    </div>

                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={createAlert}
                        disabled={!ticker || !targetPrice}
                        className="btn-primary flex-1 py-2 text-sm"
                      >
                        Create Alert
                      </button>
                      <button
                        onClick={() => setShowCreate(false)}
                        className="btn-secondary py-2 px-4 text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Ticker Extraction */}
            <div className="glass p-5">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Search size={16} className="text-primary" />
                Extract Tickers
              </h3>
              <p className="text-xs text-gray-500 mb-3">
                Auto-detect stock symbols from an uploaded document
              </p>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={docId}
                  onChange={(e) => setDocId(e.target.value)}
                  placeholder="Document ID"
                  className="input-field flex-1 text-sm"
                />
                <button
                  onClick={extractTickers}
                  disabled={!docId || loadingTickers}
                  className="btn-primary px-3 py-2 text-sm"
                >
                  {loadingTickers ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                </button>
              </div>

              {tickers.length > 0 && (
                <div className="space-y-2">
                  {tickers.map(t => (
                    <button
                      key={t.symbol}
                      onClick={() => selectTicker(t.symbol)}
                      className="w-full flex items-center gap-3 p-2.5 rounded-lg text-left hover:bg-white/5 transition-colors"
                    >
                      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <DollarSign size={14} className="text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium text-sm">{t.symbol}</span>
                          <span className="text-xs text-gray-500 truncate">{t.company}</span>
                        </div>
                        <p className="text-xs text-gray-500 truncate">{t.context}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
