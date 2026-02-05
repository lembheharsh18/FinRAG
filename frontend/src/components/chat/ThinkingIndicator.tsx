import { motion } from 'framer-motion'

export default function ThinkingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex justify-start"
    >
      <div className="message-ai flex items-center gap-2">
        <span className="text-gray-400">Thinking</span>
        <div className="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </motion.div>
  )
}
