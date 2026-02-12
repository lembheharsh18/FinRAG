import { useEffect, useCallback } from 'react'

interface ShortcutConfig {
  onSearch?: () => void
  onUpload?: () => void
  onFocusChat?: () => void
  onToggleSidebar?: () => void
}

export function useKeyboardShortcuts(config: ShortcutConfig) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {

    // Ctrl+K - Search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault()
      config.onSearch?.()
      return
    }

    // Ctrl+N - Upload
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
      e.preventDefault()
      config.onUpload?.()
      return
    }

    // Ctrl+/ - Focus chat
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault()
      config.onFocusChat?.()
      return
    }

    // Ctrl+M - Toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
      e.preventDefault()
      config.onToggleSidebar?.()
      return
    }
  }, [config])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}
