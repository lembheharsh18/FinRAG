import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, 
  Upload, 
  LogOut, 
  ChevronLeft, 
  ChevronRight,
  User,
  Settings,
  HelpCircle,
  Trash2
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

interface Document {
  id: string
  name: string
  uploadedAt: Date
  pageCount: number
}

interface SidebarProps {
  documents: Document[]
  selectedDocId: string | null
  onSelectDoc: (id: string) => void
  onUploadClick: () => void
  onDeleteDoc?: (id: string) => void
}

export default function Sidebar({ 
  documents, 
  selectedDocId, 
  onSelectDoc, 
  onUploadClick,
  onDeleteDoc 
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 280 }}
      className="h-screen flex flex-col bg-dark-50/50 border-r border-white/5"
    >
      {/* Logo */}
      <div className="p-4 flex items-center justify-between border-b border-white/5">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h1 className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                FinRAG
              </h1>
            </motion.div>
          )}
        </AnimatePresence>
        
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Upload button */}
      <div className="p-4">
        <button
          onClick={onUploadClick}
          className={`btn-primary w-full flex items-center justify-center gap-2 ${collapsed ? 'px-3' : ''}`}
        >
          <Upload size={18} />
          {!collapsed && <span>Upload Document</span>}
        </button>
      </div>

      {/* Documents list */}
      <div className="flex-1 overflow-y-auto px-2">
        <AnimatePresence>
          {!collapsed && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-xs text-gray-500 uppercase tracking-wider px-2 mb-2"
            >
              My Documents
            </motion.p>
          )}
        </AnimatePresence>

        <div className="space-y-1">
          {documents.length === 0 ? (
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-sm text-gray-500 px-2 py-4 text-center"
                >
                  No documents yet
                </motion.p>
              )}
            </AnimatePresence>
          ) : (
            documents.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="group relative"
              >
                <button
                  onClick={() => onSelectDoc(doc.id)}
                  className={`w-full ${
                    selectedDocId === doc.id ? 'sidebar-item-active' : 'sidebar-item'
                  } ${collapsed ? 'justify-center' : ''}`}
                >
                  <FileText size={18} className="flex-shrink-0" />
                  {!collapsed && (
                    <span className="truncate flex-1 text-left">{doc.name}</span>
                  )}
                </button>
                
                {/* Delete button */}
                {!collapsed && onDeleteDoc && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteDoc(doc.id)
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg 
                      opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-gray-400 
                      hover:text-red-400 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </motion.div>
            ))
          )}
        </div>
      </div>

      {/* User profile */}
      <div className="p-4 border-t border-white/5">
        <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
          {/* Avatar */}
          <div className="w-10 h-10 rounded-full bg-gradient-primary flex items-center justify-center text-white font-medium flex-shrink-0">
            {user?.photoURL ? (
              <img 
                src={user.photoURL} 
                alt={user.displayName || 'User'} 
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              user?.displayName?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U'
            )}
          </div>

          {/* User info */}
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.displayName || 'User'}
              </p>
              <p className="text-xs text-gray-400 truncate">
                {user?.email}
              </p>
            </div>
          )}

          {/* Logout button */}
          {!collapsed && (
            <button
              onClick={handleSignOut}
              className="p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white"
              title="Sign out"
            >
              <LogOut size={18} />
            </button>
          )}
        </div>

        {/* Collapsed logout */}
        {collapsed && (
          <button
            onClick={handleSignOut}
            className="mt-3 p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white w-full flex justify-center"
            title="Sign out"
          >
            <LogOut size={18} />
          </button>
        )}
      </div>
    </motion.aside>
  )
}
