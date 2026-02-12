import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, 
  Upload, 
  LogOut, 
  ChevronLeft, 
  ChevronRight,
  Trash2,
  BarChart3,
  Activity,
  GitCompare,
  Keyboard,
  Bell
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
  const [showShortcuts, setShowShortcuts] = useState(false)
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const isStocksDashboard = location.pathname === '/dashboard/stocks'
  const isAnalytics = location.pathname === '/dashboard/analytics'
  const isCompare = location.pathname === '/dashboard/compare'
  const isAlerts = location.pathname === '/dashboard/alerts'

  const navItems = [
    { id: 'stocks', path: '/dashboard/stocks', label: 'Market Dashboard', icon: BarChart3, active: isStocksDashboard },
    { id: 'compare', path: '/dashboard/compare', label: 'Compare Docs', icon: GitCompare, active: isCompare },
    { id: 'analytics', path: '/dashboard/analytics', label: 'Analytics', icon: Activity, active: isAnalytics },
    { id: 'alerts', path: '/dashboard/alerts', label: 'Alerts', icon: Bell, active: isAlerts },
  ]

  const shortcuts = [
    { keys: ['Ctrl', 'K'], action: 'Search documents' },
    { keys: ['Ctrl', 'N'], action: 'Upload new document' },
    { keys: ['Ctrl', '/'], action: 'Focus chat input' },
    { keys: ['Ctrl', 'M'], action: 'Toggle sidebar' },
    { keys: ['Esc'], action: 'Close modals' },
  ]

  return (
    <>
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

        {/* Navigation links */}
        <div className="px-2 mb-2 space-y-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium ${
                item.active 
                  ? 'bg-primary/10 text-primary border border-primary/20' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              } ${collapsed ? 'justify-center' : ''}`}
            >
              <item.icon size={18} className="flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          ))}
        </div>

        {/* Separator */}
        <div className="px-4 my-1">
          <div className="border-t border-white/5"></div>
        </div>

        {/* Documents list */}
        <div className="flex-1 overflow-y-auto px-2">
          <AnimatePresence>
            {!collapsed && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-xs text-gray-500 uppercase tracking-wider px-2 mb-2 mt-2"
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

        {/* Bottom actions */}
        <div className="p-3 border-t border-white/5 space-y-2">
          {/* Keyboard shortcuts */}
          {!collapsed && (
            <button
              onClick={() => setShowShortcuts(true)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors"
            >
              <Keyboard size={14} />
              <span>Keyboard shortcuts</span>
              <span className="ml-auto text-[10px] bg-white/5 px-1.5 py-0.5 rounded">Ctrl+/</span>
            </button>
          )}
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

      {/* Keyboard Shortcuts Modal */}
      <AnimatePresence>
        {showShortcuts && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-50"
              onClick={() => setShowShortcuts(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 glass p-6 w-96"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <Keyboard size={18} className="text-primary" />
                  Keyboard Shortcuts
                </h3>
                <button 
                  onClick={() => setShowShortcuts(false)}
                  className="text-gray-400 hover:text-white text-sm"
                >
                  ESC
                </button>
              </div>
              <div className="space-y-3">
                {shortcuts.map((shortcut, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">{shortcut.action}</span>
                    <div className="flex gap-1">
                      {shortcut.keys.map(key => (
                        <kbd 
                          key={key}
                          className="px-2 py-1 bg-white/5 border border-white/10 rounded text-xs text-gray-300 font-mono"
                        >
                          {key}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
