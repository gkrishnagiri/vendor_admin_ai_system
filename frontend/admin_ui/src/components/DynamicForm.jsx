import React, { useState } from 'react';
import { Clipboard } from 'lucide-react';

export default function DynamicForm({ schema, onSubmit, onClear }) {
  const [formData, setFormData] = useState({});

  const handleChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleKeyDown = (e) => {
    // Default to submission on Enter as requested
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="dynamic-form-card" style={{
      background: 'white',
      padding: '20px',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      border: '1px solid #e2e8f0',
      margin: '10px 0'
    }}>
      <h3 style={{ margin: '0 0 8px 0', fontSize: '1.1rem', fontWeight: 600 }}>{schema.title}</h3>
      <p style={{ margin: '0 0 20px 0', fontSize: '0.9rem', color: '#64748b' }}>{schema.description}</p>
      
      <form onSubmit={handleSubmit} onKeyDown={handleKeyDown}>
        {schema.fields.map(field => (
          <div key={field.name} style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '6px' }}>
              {field.label} {field.required && <span style={{ color: '#ef4444' }}>*</span>}
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type={field.type || 'text'}
                placeholder={field.placeholder}
                required={field.required}
                className="form-control"
                style={{ width: '100%' }}
                value={formData[field.name] || ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
              />
              <button
                type="button"
                className="btn"
                style={{ padding: '0 10px', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: 'var(--accent)' }}
                onClick={async () => {
                  const text = await navigator.clipboard.readText();
                  handleChange(field.name, text);
                }}
                title="Paste"
              >
                <Clipboard size={14} />
              </button>
            </div>
          </div>
        ))}
        
        <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
          <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
            Submit
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClear} style={{ flex: 1 }}>
            Clear
          </button>
        </div>
      </form>
    </div>
  );
}
