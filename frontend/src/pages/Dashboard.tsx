import { useState, useEffect } from 'react'
import { useNavigate, useParams, Routes, Route } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import toast from 'react-hot-toast'
import Sidebar from '../components/layout/Sidebar'
import EmptyState from '../components/dashboard/EmptyState'
import DocumentView from '../components/dashboard/DocumentView'
import UploadModal from '../components/upload/UploadModal'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

interface Document {
  id: string
  name: string
  uploadedAt: Date
  pageCount: number
  chunks?: number
}

export default function Dashboard() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { user } = useAuth()

  // Load user's documents
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await api.get('/api/collections/stats')
        // Transform the response to our document format
        const docs = response.data.documents?.map((doc: any) => ({
          id: doc.document_id,
          name: doc.filename || doc.document_id,
          uploadedAt: new Date(doc.uploaded_at || Date.now()),
          pageCount: doc.page_count || 0,
          chunks: doc.chunk_count || 0
        })) || []
        setDocuments(docs)
      } catch (error) {
        // Collection might not exist yet
        console.log('No documents found or collection not initialized')
        setDocuments([])
      } finally {
        setLoading(false)
      }
    }

    loadDocuments()
  }, [])

  const handleSelectDoc = (id: string) => {
    setSelectedDocId(id)
    navigate(`/dashboard/doc/${id}`)
  }

  const handleUploadComplete = (docId: string, docName: string) => {
    const newDoc: Document = {
      id: docId,
      name: docName,
      uploadedAt: new Date(),
      pageCount: 0
    }
    setDocuments(prev => [newDoc, ...prev])
    setShowUploadModal(false)
    toast.success('Document uploaded successfully!')
    handleSelectDoc(docId)
  }

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await api.delete(`/api/documents/${docId}`)
      setDocuments(prev => prev.filter(d => d.id !== docId))
      if (selectedDocId === docId) {
        setSelectedDocId(null)
        navigate('/dashboard')
      }
      toast.success('Document deleted')
    } catch (error) {
      toast.error('Failed to delete document')
    }
  }

  const selectedDoc = documents.find(d => d.id === selectedDocId)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDoc={handleSelectDoc}
        onUploadClick={() => setShowUploadModal(true)}
        onDeleteDoc={handleDeleteDoc}
      />

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex items-center justify-center"
            >
              <div className="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </motion.div>
          ) : selectedDocId && selectedDoc ? (
            <motion.div
              key={selectedDocId}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <DocumentView document={selectedDoc} />
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full"
            >
              <EmptyState onUploadClick={() => setShowUploadModal(true)} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Upload modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onComplete={handleUploadComplete}
      />
    </div>
  )
}
