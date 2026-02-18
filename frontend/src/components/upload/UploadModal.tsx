import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { X, Upload, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { api } from '../../lib/api'

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (documentId: string, documentName: string) => void
}

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'indexing' | 'complete' | 'error'

export default function UploadModal({ isOpen, onClose, onComplete }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<UploadStatus>('idle')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [_documentId, setDocumentId] = useState('')

  const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0]
      if (rejection.file.size > MAX_FILE_SIZE) {
        setError('File is too large. Maximum size is 50MB.')
      } else {
        setError('Please upload a PDF file.')
      }
      return
    }

    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      setError('')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
  })

  const handleUpload = async () => {
    if (!file) return

    setStatus('uploading')
    setProgress(0)
    setError('')

    try {
      // Create form data
      const formData = new FormData()
      formData.append('file', file)

      // Upload file (backend now auto-indexes during upload)
      const uploadResponse = await api.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
          setProgress(percent)
        },
      })

      const docId = uploadResponse.data.document_id
      setDocumentId(docId)
      
      // Show processing state briefly for UX
      setStatus('processing')
      await new Promise(r => setTimeout(r, 300))
      
      setStatus('indexing')
      await new Promise(r => setTimeout(r, 300))

      setStatus('complete')
      
      // Wait a moment then complete
      setTimeout(() => {
        onComplete(docId, file.name)
        resetState()
      }, 1000)

    } catch (err: any) {
      console.error('Upload error:', err)
      setError(err.response?.data?.detail?.error || 'Upload failed. Please try again.')
      setStatus('error')
    }
  }

  const resetState = () => {
    setFile(null)
    setStatus('idle')
    setProgress(0)
    setError('')
    setDocumentId('')
  }

  const handleClose = () => {
    if (status === 'uploading' || status === 'processing' || status === 'indexing') {
      if (!confirm('Upload in progress. Are you sure you want to cancel?')) return
    }
    resetState()
    onClose()
  }

  const getStatusText = () => {
    switch (status) {
      case 'uploading': return `Uploading... ${progress}%`
      case 'processing': return 'Processing PDF...'
      case 'indexing': return 'Indexing vectors...'
      case 'complete': return 'Complete!'
      case 'error': return 'Upload failed'
      default: return ''
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="glass-card w-full max-w-lg relative z-10"
          >
            {/* Close button */}
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white"
            >
              <X size={20} />
            </button>

            <h2 className="text-2xl font-semibold text-white mb-2">Upload Document</h2>
            <p className="text-gray-400 mb-6">
              Upload a PDF financial document to analyze
            </p>

            {/* Error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6"
              >
                <AlertCircle size={18} />
                <span className="text-sm">{error}</span>
              </motion.div>
            )}

            {/* Drop zone */}
            {status === 'idle' && (
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                  isDragActive 
                    ? 'border-primary bg-primary/10' 
                    : file 
                      ? 'border-green-500/50 bg-green-500/10' 
                      : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                }`}
              >
                <input {...getInputProps()} />
                
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="text-green-400" size={24} />
                    <div className="text-left">
                      <p className="text-white font-medium">{file.name}</p>
                      <p className="text-gray-400 text-sm">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                ) : (
                  <>
                    <Upload className="mx-auto text-gray-400 mb-4" size={40} />
                    <p className="text-white mb-2">
                      {isDragActive ? 'Drop the file here' : 'Drag & drop your PDF here'}
                    </p>
                    <p className="text-gray-500 text-sm">
                      or click to browse (max 50MB)
                    </p>
                  </>
                )}
              </div>
            )}

            {/* Progress state */}
            {(status === 'uploading' || status === 'processing' || status === 'indexing') && (
              <div className="py-8">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <Loader2 className="animate-spin text-primary" size={24} />
                  <span className="text-white font-medium">{getStatusText()}</span>
                </div>
                
                {status === 'uploading' && (
                  <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      className="h-full bg-gradient-primary"
                    />
                  </div>
                )}

                <div className="flex justify-center gap-4 mt-6 text-sm text-gray-400">
                  <span className={status === 'uploading' ? 'text-primary' : 'text-green-400'}>
                    ✓ Upload
                  </span>
                  <span className={status === 'processing' ? 'text-primary' : status === 'indexing' ? 'text-green-400' : ''}>
                    → Process
                  </span>
                  <span className={status === 'indexing' ? 'text-primary' : ''}>
                    → Index
                  </span>
                </div>
              </div>
            )}

            {/* Complete state */}
            {status === 'complete' && (
              <div className="py-8 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring' }}
                  className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4"
                >
                  <CheckCircle className="text-green-400" size={32} />
                </motion.div>
                <p className="text-white font-medium">Document ready!</p>
                <p className="text-gray-400 text-sm">Redirecting to chat...</p>
              </div>
            )}

            {/* Actions */}
            {status === 'idle' && (
              <div className="flex gap-3 mt-6">
                <button onClick={handleClose} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!file}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  <Upload size={18} />
                  Upload
                </button>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
