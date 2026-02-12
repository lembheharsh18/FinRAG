import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  TrendingUp, TrendingDown, RefreshCw, BarChart3, 
  ArrowUpRight, ArrowDownRight, Activity, DollarSign,
  Clock, Zap, ChevronRight
} from 'lucide-react'
import { api } from '../lib/api'

// ————— Types —————

interface IndexData {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  sparkline: number[]
}

interface StockMover {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  volume: number
}

interface MarketData {
  indices: IndexData[]
  top_gainers: StockMover[]
  top_losers: StockMover[]
  trending: StockMover[]
  last_updated: string
}

interface PricePoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// ————— Mini Sparkline Component —————

function Sparkline({ data, positive }: { data: number[]; positive: boolean }) {
  if (!data || data.length < 2) return null
  
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const width = 120
  const height = 40
  const padding = 2

  const points = data.map((val, i) => {
    const x = padding + (i / (data.length - 1)) * (width - padding * 2)
    const y = height - padding - ((val - min) / range) * (height - padding * 2)
    return `${x},${y}`
  }).join(' ')

  const gradientId = `sparkline-${Math.random().toString(36).slice(2)}`

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={positive ? '#10b981' : '#ef4444'} stopOpacity={0.3} />
          <stop offset="100%" stopColor={positive ? '#10b981' : '#ef4444'} stopOpacity={0} />
        </linearGradient>
      </defs>
      <polyline
        points={points}
        fill="none"
        stroke={positive ? '#10b981' : '#ef4444'}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Area fill */}
      <polygon
        points={`${padding},${height - padding} ${points} ${width - padding},${height - padding}`}
        fill={`url(#${gradientId})`}
      />
    </svg>
  )
}

// ————— Mini Bar Chart for Volume —————

function VolumeBar({ volume }: { volume: number }) {
  const formatted = volume >= 1e9
    ? `${(volume / 1e9).toFixed(1)}B`
    : volume >= 1e6
    ? `${(volume / 1e6).toFixed(1)}M`
    : volume >= 1e3
    ? `${(volume / 1e3).toFixed(0)}K`
    : volume.toString()

  return (
    <span className="text-xs text-gray-400 font-mono">{formatted}</span>
  )
}

// ————— Price Chart Component —————

function PriceChart({ symbol, name }: { symbol: string; name: string }) {
  const [data, setData] = useState<PricePoint[]>([])
  const [period, setPeriod] = useState('1mo')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true)
      try {
        const res = await api.get(`/api/stocks/price-history/${symbol}`, {
          params: { period, interval: period === '1d' ? '5m' : '1d' }
        })
        setData(res.data.data || [])
      } catch {
        setData([])
      } finally {
        setLoading(false)
      }
    }
    fetchHistory()
  }, [symbol, period])

  if (loading) {
    return (
      <div className="h-48 flex items-center justify-center">
        <div className="thinking-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
        No chart data available
      </div>
    )
  }

  // Render a simple area chart
  const closes = data.map(d => d.close)
  const min = Math.min(...closes) * 0.998
  const max = Math.max(...closes) * 1.002
  const range = max - min || 1
  const w = 600
  const h = 180
  const pad = 4

  const points = closes.map((val, i) => {
    const x = pad + (i / (closes.length - 1)) * (w - pad * 2)
    const y = h - pad - ((val - min) / range) * (h - pad * 2)
    return `${x},${y}`
  }).join(' ')

  const isPositive = closes[closes.length - 1] >= closes[0]

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-white font-semibold">{name}</h4>
          <p className="text-gray-400 text-xs">{symbol}</p>
        </div>
        <div className="flex gap-1">
          {['1d', '5d', '1mo', '3mo', '1y'].map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-2 py-1 text-xs rounded-md transition-all ${
                period === p
                  ? 'bg-primary/20 text-primary'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={isPositive ? '#10b981' : '#ef4444'} stopOpacity={0.2} />
            <stop offset="100%" stopColor={isPositive ? '#10b981' : '#ef4444'} stopOpacity={0} />
          </linearGradient>
        </defs>
        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map(pct => (
          <line
            key={pct}
            x1={pad} y1={h - pad - pct * (h - pad * 2)}
            x2={w - pad} y2={h - pad - pct * (h - pad * 2)}
            stroke="rgba(255,255,255,0.05)" strokeWidth={1}
          />
        ))}
        <polygon
          points={`${pad},${h - pad} ${points} ${w - pad},${h - pad}`}
          fill="url(#chartGrad)"
        />
        <polyline
          points={points}
          fill="none"
          stroke={isPositive ? '#10b981' : '#ef4444'}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>{data[0]?.date}</span>
        <span>{data[data.length - 1]?.date}</span>
      </div>
    </div>
  )
}

// ————— Main Page —————

export default function StockDashboard() {
  const [marketData, setMarketData] = useState<MarketData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedChart, setSelectedChart] = useState<{ symbol: string; name: string } | null>(null)

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    
    try {
      const res = await api.get('/api/stocks/market')
      setMarketData(res.data)
      
      // Auto-select first index for chart if none selected
      if (!selectedChart && res.data.indices?.length) {
        setSelectedChart({
          symbol: res.data.trending?.[0]?.symbol || 'AAPL',
          name: res.data.trending?.[0]?.name || 'Apple',
        })
      }
    } catch (err) {
      console.error('Failed to fetch market data:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [selectedChart])

  useEffect(() => {
    fetchData()
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => fetchData(true), 300000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Activity className="mx-auto text-primary mb-4 animate-pulse" size={48} />
          <p className="text-gray-400">Loading market data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="text-primary" size={28} />
              Market Dashboard
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Live stock market overview and analytics
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {marketData?.last_updated && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Clock size={12} />
                {new Date(marketData.last_updated).toLocaleTimeString()}
              </span>
            )}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="btn-secondary px-3 py-2 flex items-center gap-2 text-sm"
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              Refresh
            </motion.button>
          </div>
        </div>

        {/* Market Indices */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <AnimatePresence>
            {marketData?.indices.map((index, i) => (
              <motion.div
                key={index.symbol}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass p-4 hover:bg-white/[0.04] transition-all cursor-pointer group"
                onClick={() => setSelectedChart({ symbol: index.symbol, name: index.name })}
              >
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-400 font-medium">{index.name}</p>
                  <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                    index.change >= 0 
                      ? 'bg-green-500/10 text-green-400' 
                      : 'bg-red-500/10 text-red-400'
                  }`}>
                    {index.change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {Math.abs(index.change_percent).toFixed(2)}%
                  </div>
                </div>
                <p className="text-2xl font-bold text-white mb-2">
                  {index.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
                <div className="flex items-center justify-between">
                  <span className={`text-sm ${index.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)}
                  </span>
                  <Sparkline data={index.sparkline} positive={index.change >= 0} />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Chart + Trending Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Price chart (2/3) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-2 glass p-6"
          >
            {selectedChart ? (
              <PriceChart symbol={selectedChart.symbol} name={selectedChart.name} />
            ) : (
              <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
                Select a stock or index to view chart
              </div>
            )}
          </motion.div>

          {/* Trending stocks (1/3) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass p-4"
          >
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <Zap className="text-yellow-400" size={16} />
              Trending by Volume
            </h3>
            <div className="space-y-2">
              {marketData?.trending.map((stock, i) => (
                <motion.div
                  key={stock.symbol}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.05 }}
                  onClick={() => setSelectedChart({ symbol: stock.symbol, name: stock.name })}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-all group"
                >
                  <span className="text-xs text-gray-500 w-4">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{stock.symbol}</p>
                    <p className="text-gray-500 text-xs truncate">{stock.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-white text-sm font-mono">${stock.price.toFixed(2)}</p>
                    <div className={`flex items-center justify-end gap-0.5 text-xs ${
                      stock.change >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {stock.change >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                      {Math.abs(stock.change_percent).toFixed(2)}%
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-gray-600 group-hover:text-gray-400 transition-colors" />
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Top Gainers & Losers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gainers */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="glass p-4"
          >
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <TrendingUp className="text-green-400" size={18} />
              Top Gainers
            </h3>
            <div className="space-y-1">
              {marketData?.top_gainers.map((stock) => (
                <div 
                  key={stock.symbol}
                  onClick={() => setSelectedChart({ symbol: stock.symbol, name: stock.name })}
                  className="flex items-center p-3 rounded-lg hover:bg-white/5 cursor-pointer transition-all"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-semibold text-sm">{stock.symbol}</span>
                      <span className="text-gray-500 text-xs truncate">{stock.name}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <VolumeBar volume={stock.volume} />
                    <span className="text-white font-mono text-sm w-20 text-right">
                      ${stock.price.toFixed(2)}
                    </span>
                    <span className="bg-green-500/10 text-green-400 text-xs font-semibold px-2 py-1 rounded-md w-20 text-center">
                      +{stock.change_percent.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Losers */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="glass p-4"
          >
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <TrendingDown className="text-red-400" size={18} />
              Top Losers
            </h3>
            <div className="space-y-1">
              {marketData?.top_losers.map((stock) => (
                <div 
                  key={stock.symbol}
                  onClick={() => setSelectedChart({ symbol: stock.symbol, name: stock.name })}
                  className="flex items-center p-3 rounded-lg hover:bg-white/5 cursor-pointer transition-all"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-semibold text-sm">{stock.symbol}</span>
                      <span className="text-gray-500 text-xs truncate">{stock.name}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <VolumeBar volume={stock.volume} />
                    <span className="text-white font-mono text-sm w-20 text-right">
                      ${stock.price.toFixed(2)}
                    </span>
                    <span className="bg-red-500/10 text-red-400 text-xs font-semibold px-2 py-1 rounded-md w-20 text-center">
                      {stock.change_percent.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Footer info */}
        <div className="text-center pb-4">
          <p className="text-xs text-gray-600">
            Data provided by Yahoo Finance • Auto-refreshes every 5 minutes • 
            <DollarSign size={10} className="inline mx-1" />
            Prices are delayed
          </p>
        </div>
      </div>
    </div>
  )
}
