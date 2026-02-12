import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../../lib/api'

interface ExportButtonProps {
  documentId: string
  documentName: string
  messages: {
    type: 'user' | 'ai'
    content: string
    sources?: any[]
  }[]
}

export default function ExportButton({ documentId, documentName, messages }: ExportButtonProps) {
  const [loading, setLoading] = useState(false)

  const handleExport = async () => {
    if (messages.length === 0) {
      toast.error('No conversation to export')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/api/export/report', {
        document_id: documentId,
        document_name: documentName,
        messages: messages.map(m => ({
          role: m.type === 'user' ? 'user' : 'ai',
          content: m.content,
          sources: m.sources
        })),
        include_summary: true
      })

      // Download as markdown file
      const blob = new Blob([response.data.content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `FinRAG_Report_${documentName.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success('Report exported successfully!')
    } catch (err) {
      toast.error('Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={loading || messages.length === 0}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all disabled:opacity-50"
      title="Export conversation as report"
    >
      {loading ? (
        <Loader2 size={12} className="animate-spin" />
      ) : (
        <Download size={12} />
      )}
      Export
    </button>
  )
}
