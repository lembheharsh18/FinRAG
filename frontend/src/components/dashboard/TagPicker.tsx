import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Tag, Plus, X } from 'lucide-react'
import { api } from '../../lib/api'

interface TagPickerProps {
  documentId: string
}

export default function TagPicker({ documentId }: TagPickerProps) {
  const [tags, setTags] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchTags()
  }, [documentId])

  const fetchTags = async () => {
    try {
      const response = await api.get(`/api/documents/${documentId}/tags`)
      setTags(response.data.tags || [])
    } catch {
      // Tags might not exist yet
    }
  }

  const addTag = async () => {
    const newTag = input.trim().toLowerCase()
    if (!newTag || tags.includes(newTag)) {
      setInput('')
      return
    }

    const updatedTags = [...tags, newTag]
    setTags(updatedTags)
    setInput('')

    try {
      await api.post(`/api/documents/${documentId}/tags`, {
        document_id: documentId,
        tags: updatedTags
      })
    } catch {
      setTags(tags) // Revert
    }
  }

  const removeTag = async (tag: string) => {
    const updatedTags = tags.filter(t => t !== tag)
    setTags(updatedTags)

    try {
      await api.delete(`/api/documents/${documentId}/tags/${tag}`)
    } catch {
      setTags(tags) // Revert
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
    if (e.key === 'Escape') {
      setIsAdding(false)
      setInput('')
    }
  }

  const tagColors = [
    'bg-blue-500/15 text-blue-400 border-blue-500/20',
    'bg-purple-500/15 text-purple-400 border-purple-500/20',
    'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    'bg-amber-500/15 text-amber-400 border-amber-500/20',
    'bg-pink-500/15 text-pink-400 border-pink-500/20',
    'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  ]

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Tag size={14} className="text-gray-500 flex-shrink-0" />
      
      <AnimatePresence>
        {tags.map((tag, i) => (
          <motion.span
            key={tag}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${
              tagColors[i % tagColors.length]
            }`}
          >
            {tag}
            <button 
              onClick={() => removeTag(tag)}
              className="hover:opacity-70 transition-opacity"
            >
              <X size={10} />
            </button>
          </motion.span>
        ))}
      </AnimatePresence>

      {isAdding ? (
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => { addTag(); setIsAdding(false) }}
          placeholder="tag name"
          className="bg-transparent text-xs text-white outline-none border-b border-white/20 pb-0.5 w-20"
          autoFocus
        />
      ) : (
        <button 
          onClick={() => setIsAdding(true)}
          className="p-0.5 rounded hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
          title="Add tag"
        >
          <Plus size={12} />
        </button>
      )}
    </div>
  )
}
