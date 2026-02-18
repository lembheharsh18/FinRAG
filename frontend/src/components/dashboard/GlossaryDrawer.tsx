import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Search, X, ChevronDown, ChevronRight, Calculator } from 'lucide-react'
import { api } from '../../lib/api'

interface Term {
  term: string
  category: string
  definition: string
  formula?: string
  example?: string
  why_it_matters: string
}

interface GlossaryDrawerProps {
  isOpen: boolean
  onClose: () => void
}

export default function GlossaryDrawer({ isOpen, onClose }: GlossaryDrawerProps) {
  const [terms, setTerms] = useState<Term[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedTerm, setExpandedTerm] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen && terms.length === 0) {
      loadTerms()
    }
  }, [isOpen])

  const loadTerms = async () => {
    setLoading(true)
    try {
      const resp = await api.get('/api/glossary')
      setTerms(resp.data)
    } catch {
      console.error('Failed to load glossary')
    } finally {
      setLoading(false)
    }
  }

  const categories = [...new Set(terms.map(t => t.category))]

  const filteredTerms = terms.filter(t => {
    const matchesSearch = !searchQuery || 
      t.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.definition.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = !selectedCategory || t.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const groupedTerms = filteredTerms.reduce((acc, term) => {
    if (!acc[term.category]) acc[term.category] = []
    acc[term.category].push(term)
    return acc
  }, {} as Record<string, Term[]>)

  const categoryColors: Record<string, string> = {
    'Profitability': 'text-green-400 bg-green-400/10',
    'Valuation': 'text-blue-400 bg-blue-400/10',
    'Leverage': 'text-red-400 bg-red-400/10',
    'Growth': 'text-emerald-400 bg-emerald-400/10',
    'Financial Statements': 'text-purple-400 bg-purple-400/10',
    'Regulatory': 'text-orange-400 bg-orange-400/10',
    'Market': 'text-cyan-400 bg-cyan-400/10',
    'Risk': 'text-yellow-400 bg-yellow-400/10',
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-50"
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-[420px] max-w-[90vw] glass z-50 flex flex-col border-l border-white/10"
          >
            {/* Header */}
            <div className="p-5 border-b border-white/5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <BookOpen size={20} className="text-primary" />
                  Financial Glossary
                </h3>
                <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white">
                  <X size={18} />
                </button>
              </div>

              {/* Search */}
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search terms..."
                  className="input-field !pl-10 !py-2.5 text-sm"
                />
              </div>

              {/* Category pills */}
              <div className="flex flex-wrap gap-1.5 mt-3">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                    !selectedCategory ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  All
                </button>
                {categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                      selectedCategory === cat ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Terms list */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="thinking-dots"><span></span><span></span><span></span></div>
                </div>
              ) : (
                Object.entries(groupedTerms).map(([category, categoryTerms]) => (
                  <div key={category}>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded ${categoryColors[category] || 'text-gray-400 bg-gray-400/10'}`}>
                        {category}
                      </span>
                      <span className="text-gray-600">{categoryTerms.length}</span>
                    </h4>

                    <div className="space-y-1.5">
                      {categoryTerms.map(term => (
                        <motion.div
                          key={term.term}
                          layout
                          className="glass rounded-xl overflow-hidden"
                        >
                          <button
                            onClick={() => setExpandedTerm(expandedTerm === term.term ? null : term.term)}
                            className="w-full flex items-center gap-2 p-3 text-left hover:bg-white/5 transition-colors"
                          >
                            {expandedTerm === term.term ? (
                              <ChevronDown size={14} className="text-primary flex-shrink-0" />
                            ) : (
                              <ChevronRight size={14} className="text-gray-500 flex-shrink-0" />
                            )}
                            <span className="text-sm font-medium text-white flex-1">{term.term}</span>
                          </button>

                          <AnimatePresence>
                            {expandedTerm === term.term && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden"
                              >
                                <div className="px-3 pb-3 space-y-3">
                                  <p className="text-sm text-gray-300 leading-relaxed">{term.definition}</p>

                                  {term.formula && (
                                    <div className="flex items-start gap-2 p-2.5 bg-primary/5 rounded-lg border border-primary/10">
                                      <Calculator size={14} className="text-primary mt-0.5 flex-shrink-0" />
                                      <div>
                                        <p className="text-xs text-gray-400 font-medium">Formula</p>
                                        <p className="text-sm text-primary font-mono">{term.formula}</p>
                                      </div>
                                    </div>
                                  )}

                                  {term.example && (
                                    <div className="p-2.5 bg-white/5 rounded-lg">
                                      <p className="text-xs text-gray-400 font-medium mb-1">Example</p>
                                      <p className="text-xs text-gray-300">{term.example}</p>
                                    </div>
                                  )}

                                  <div className="p-2.5 bg-emerald-500/5 rounded-lg border border-emerald-500/10">
                                    <p className="text-xs text-emerald-400 font-medium mb-1">Why It Matters</p>
                                    <p className="text-xs text-gray-300 leading-relaxed">{term.why_it_matters}</p>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                ))
              )}

              {!loading && filteredTerms.length === 0 && (
                <div className="text-center py-8">
                  <Search size={32} className="mx-auto text-gray-600 mb-3" />
                  <p className="text-sm text-gray-500">No terms found for "{searchQuery}"</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-white/5 text-center">
              <p className="text-xs text-gray-500">{terms.length} financial terms • Curated for retail investors</p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
