import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { UploadCloud } from 'lucide-react'

export default function DocumentUploader() {
  const [taxonomies, setTaxonomies] = useState([])
  
  // Selected hierarchy
  const [bu, setBu] = useState('')
  const [area, setArea] = useState('')
  const [func, setFunc] = useState('')
  const [app, setApp] = useState('')
  
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchTaxonomy()
  }, [])

  const fetchTaxonomy = async () => {
    try {
      const res = await axios.get('/api/taxonomy')
      setTaxonomies(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  // Derive available options based on selections
  const uniqueBUs = [...new Set(taxonomies.map(t => t.business_unit))]
  
  const availableAreas = [...new Set(taxonomies
    .filter(t => t.business_unit === bu)
    .map(t => t.business_area))]

  const availableFuncs = [...new Set(taxonomies
    .filter(t => t.business_unit === bu && t.business_area === area)
    .map(t => t.business_function))]



  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) {
      setMessage("Please select a file.")
      return
    }
    setUploading(true)
    setMessage('')
    
    const formData = new FormData()
    formData.append("file", file)
    if (bu) formData.append("business_unit", bu)
    if (area) formData.append("business_area", area)
    if (func) formData.append("business_function", func)
    if (app) formData.append("application_name", app)

    try {
      await axios.post('/api/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setMessage("Upload successful!")
      setFile(null)
    } catch (err) {
      setMessage("Upload failed: " + (err.response?.data?.detail || err.message))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">Upload Documents</h1>
      <div className="card">
        <form onSubmit={handleUpload}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="form-group">
              <label className="form-label">Business Unit</label>
              <select className="form-control" value={bu} onChange={e => {setBu(e.target.value); setArea(''); setFunc(''); setApp('');}}>
                <option value="">Select BU...</option>
                {uniqueBUs.map(opt => <option key={opt}>{opt}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Business Area</label>
              <select className="form-control" value={area} onChange={e => {setArea(e.target.value); setFunc(''); setApp('');}} disabled={!bu}>
                <option value="">Select Area...</option>
                {availableAreas.map(opt => <option key={opt}>{opt}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Business Function</label>
              <select className="form-control" value={func} onChange={e => {setFunc(e.target.value); setApp('');}} disabled={!area}>
                <option value="">Select Function...</option>
                {availableFuncs.map(opt => <option key={opt}>{opt}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Application Name <span style={{fontWeight: 400, color: 'var(--text-muted)', fontSize: '0.85em'}}>(optional)</span></label>
              <input
                className="form-control"
                type="text"
                placeholder="e.g. SAP Ariba, Coupa, ServiceNow..."
                value={app}
                onChange={e => setApp(e.target.value)}
              />
            </div>
          </div>
          
          <div className="form-group mt-4" style={{ marginTop: '20px' }}>
            <label className="form-label">Document File</label>
            <div className="file-dropzone">
              <input 
                type="file" 
                id="file" 
                style={{display: 'none'}} 
                onChange={(e) => setFile(e.target.files[0])} 
              />
              <label htmlFor="file" style={{cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px'}}>
                <UploadCloud size={48} color="var(--accent)" />
                {file ? <span>Selected: {file.name}</span> : <span>Click here to select a document to upload</span>}
              </label>
            </div>
          </div>

          {message && <div style={{marginBottom: '20px', color: message.includes('failed') ? 'var(--danger)' : '#10b981'}}>{message}</div>}

          <button type="submit" className="btn" disabled={uploading}>
            {uploading ? 'Uploading and embedding chunks...' : 'Upload & Process'}
          </button>
        </form>
      </div>
    </div>
  )
}
