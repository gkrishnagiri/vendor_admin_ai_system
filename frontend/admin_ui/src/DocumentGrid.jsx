import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Trash2 } from 'lucide-react'

export default function DocumentGrid() {
  const [documents, setDocuments] = useState([])
  const [selectedDocs, setSelectedDocs] = useState(new Set())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const res = await axios.get('/api/documents')
      setDocuments(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const toggleSelect = (id) => {
    const nextSet = new Set(selectedDocs)
    if (nextSet.has(id)) {
      nextSet.delete(id)
    } else {
      nextSet.add(id)
    }
    setSelectedDocs(nextSet)
  }

  const toggleSelectAll = () => {
    if (selectedDocs.size === documents.length) {
      setSelectedDocs(new Set())
    } else {
      setSelectedDocs(new Set(documents.map(d => d.id)))
    }
  }

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete these documents? Vector chunks will be permanently removed.")) return
    
    try {
      for (const id of selectedDocs) {
        await axios.delete(`/api/documents/${id}`)
      }
      setSelectedDocs(new Set())
      fetchDocuments()
    } catch (err) {
      alert("Error deleting: " + err.message)
    }
  }

  return (
    <div>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px'}}>
        <h1 className="page-title" style={{marginBottom: 0}}>Ingested Documents</h1>
        <button 
          className="btn btn-danger" 
          disabled={selectedDocs.size === 0}
          onClick={handleDelete}
        >
          <Trash2 size={16} /> Delete Selected ({selectedDocs.size})
        </button>
      </div>

      <div className="card" style={{padding: 0}}>
        {loading ? (
          <div style={{padding: '40px', textAlign: 'center'}}>Loading data...</div>
        ) : documents.length === 0 ? (
          <div style={{padding: '40px', textAlign: 'center', color: 'var(--text-muted)'}}>No documents found. Upload one to get started!</div>
        ) : (
          <div className="table-scroll-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{width: '40px'}}>
                    <input 
                      type="checkbox" 
                      checked={selectedDocs.size === documents.length && documents.length > 0} 
                      onChange={toggleSelectAll} 
                    />
                  </th>
                  <th>File Name</th>
                  <th>Business Unit</th>
                  <th>Business Area</th>
                  <th>Business Function</th>
                  <th>Application Name</th>
                  <th>Upload Date</th>
                </tr>
              </thead>
              <tbody>
                {documents.map(doc => (
                  <tr key={doc.id}>
                    <td>
                      <input 
                        type="checkbox" 
                        checked={selectedDocs.has(doc.id)} 
                        onChange={() => toggleSelect(doc.id)} 
                      />
                    </td>
                    <td style={{fontWeight: 500}}>{doc.name}</td>
                    <td>{doc.business_unit || '-'}</td>
                    <td>{doc.business_area || '-'}</td>
                    <td>{doc.business_function || '-'}</td>
                    <td>{doc.application_name || '-'}</td>
                    <td style={{color: 'var(--text-muted)'}}>{new Date(doc.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
