import React from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layers, Settings, FileUp, MessageSquare } from 'lucide-react'
import DocumentUploader from './DocumentUploader'
import DocumentGrid from './DocumentGrid'
import SettingsPanel from './SettingsPanel'
import ChatPanel from './ChatPanel'
import './index.css'

function Sidebar() {
  const location = useLocation()
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <Layers className="text-accent" />
        Admin Console
      </div>
      <div className="sidebar-nav">
        <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
          <FileUp size={20} />
          Document Upload
        </Link>
        <Link to="/documents" className={`nav-link ${location.pathname === '/documents' ? 'active' : ''}`}>
          <Layers size={20} />
          Documents List
        </Link>
        <Link to="/chat" className={`nav-link ${location.pathname === '/chat' ? 'active' : ''}`}>
          <MessageSquare size={20} />
          AI Chat
        </Link>
        <Link to="/settings" className={`nav-link ${location.pathname === '/settings' ? 'active' : ''}`}>
          <Settings size={20} />
          Settings
        </Link>
      </div>
    </div>
  )
}

function App() {
  const location = typeof window !== 'undefined' ? window.location.pathname : '/'
  const isChat = location === '/chat'

  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  )
}

function AppInner() {
  const location = useLocation()
  const isChat = location.pathname === '/chat'

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content" style={isChat ? { padding: 0, overflow: 'hidden' } : {}}>
        <Routes>
          <Route path="/" element={<DocumentUploader />} />
          <Route path="/documents" element={<DocumentGrid />} />
          <Route path="/chat" element={<ChatPanel />} />
          <Route path="/settings" element={<SettingsPanel />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
