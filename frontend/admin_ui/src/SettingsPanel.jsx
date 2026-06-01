import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Save } from 'lucide-react'

export default function SettingsPanel() {
  const [settings, setSettings] = useState({
    llm_model: 'gpt-4o-mini',
    embedding_model: 'text-embedding-3-small',
    chunk_size: '1000',
    chunk_overlap: '200',
    show_debug_panel: 'true'
  })
  
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const res = await axios.get('/api/settings')
      if (Object.keys(res.data).length > 0) {
        setSettings(prev => ({...prev, ...res.data}))
      }
    } catch (e) {
      console.error(e)
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    
    // Convert object to list of Key/Value pairs
    const updates = Object.keys(settings).map(key => ({
      key,
      value: String(settings[key])
    }))

    try {
      await axios.post('/api/settings', updates)
      setMessage("Settings saved successfully!")
    } catch (err) {
      setMessage("Save failed: " + err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (e) => {
    setSettings({...settings, [e.target.name]: e.target.value})
  }

  const handleToggle = (e) => {
    setSettings({...settings, [e.target.name]: e.target.checked ? 'true' : 'false'})
  }

  return (
    <div>
      <h1 className="page-title">Global Configuration</h1>
      <div className="card" style={{maxWidth: '600px'}}>
        <form onSubmit={handleSave}>
          <div className="form-group">
            <label className="form-label">Primary LLM Engine</label>
            <select name="llm_model" className="form-control" value={settings.llm_model} onChange={handleChange}>
              <option value="gpt-4o-mini">GPT-4o-mini (Default, Best value)</option>
              <option value="gpt-4o">GPT-4o (High Performance)</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Faster, Cheaper)</option>
              <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
              <option value="llama-3-70b">Llama 3 70B (Local/Open Source)</option>
            </select>
            <p style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '8px'}}>The model used by the orchestrator and action planners.</p>
          </div>

          <div className="form-group">
            <label className="form-label">Embedding Model</label>
            <select name="embedding_model" className="form-control" value={settings.embedding_model} onChange={handleChange}>
              <option value="text-embedding-3-small">text-embedding-3-small (Default)</option>
              <option value="text-embedding-3-large">text-embedding-3-large</option>
              <option value="text-embedding-ada-002">text-embedding-ada-002</option>
            </select>
          </div>
          
          <div className="form-group">
            <label className="form-label">Vector Chunk Size: {settings.chunk_size} chars</label>
            <input 
              type="range" 
              name="chunk_size" 
              min="200" 
              max="4000" 
              step="100" 
              style={{width: '100%'}} 
              value={settings.chunk_size} 
              onChange={handleChange} 
            />
          </div>

          <div className="form-group">
            <label className="form-label">Chunk Overlap: {settings.chunk_overlap} chars</label>
            <input 
              type="range" 
              name="chunk_overlap" 
              min="0" 
              max="1000" 
              step="50" 
              style={{width: '100%'}} 
              value={settings.chunk_overlap} 
              onChange={handleChange} 
            />
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0' }}>
            <input
              type="checkbox"
              id="show_debug_panel"
              name="show_debug_panel"
              checked={settings.show_debug_panel === 'true'}
              onChange={handleToggle}
              style={{ width: 18, height: 18, accentColor: 'var(--accent)', cursor: 'pointer' }}
            />
            <label htmlFor="show_debug_panel" className="form-label" style={{ marginBottom: 0, cursor: 'pointer' }}>
              Show Debug Panel in Chat UI
              <span style={{ display: 'block', fontWeight: 400, fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 2 }}>
                Displays the backend print/trace output alongside chat responses. Disable when the agent is stable.
              </span>
            </label>
          </div>


          <button type="submit" className="btn" disabled={saving}>
            <Save size={18} /> {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </form>
      </div>
    </div>
  )
}
