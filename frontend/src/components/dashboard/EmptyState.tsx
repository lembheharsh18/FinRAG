import { motion } from 'framer-motion'
import { Upload, FileText, MessageSquare, Sparkles } from 'lucide-react'

interface EmptyStateProps {
  onUploadClick: () => void
}

export default function EmptyState({ onUploadClick }: EmptyStateProps) {
  const features = [
    {
      icon: FileText,
      title: 'Upload PDFs',
      description: 'Support for financial reports, earnings calls, and more'
    },
    {
      icon: MessageSquare,
      title: 'Ask Questions',
      description: 'Natural language queries about your documents'
    },
    {
      icon: Sparkles,
      title: 'AI Answers',
      description: 'Get accurate answers with source citations'
    }
  ]

  return (
    <div className="h-full flex flex-col items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-xl"
      >
        {/* Icon */}
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring' }}
          className="w-24 h-24 rounded-full bg-gradient-primary/20 flex items-center justify-center mx-auto mb-8"
        >
          <FileText size={40} className="text-primary" />
        </motion.div>

        {/* Heading */}
        <h2 className="text-3xl font-bold text-white mb-4">
          Welcome to FinRAG
        </h2>
        <p className="text-gray-400 text-lg mb-8">
          Upload your first financial document to start asking questions
        </p>

        {/* Upload button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onUploadClick}
          className="btn-primary inline-flex items-center gap-3 text-lg px-8 py-4"
        >
          <Upload size={22} />
          Upload Document
        </motion.button>

        {/* Features */}
        <div className="grid grid-cols-3 gap-6 mt-12">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              className="glass p-6 text-center"
            >
              <feature.icon className="mx-auto text-primary mb-3" size={28} />
              <h3 className="text-white font-medium mb-2">{feature.title}</h3>
              <p className="text-gray-400 text-sm">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
