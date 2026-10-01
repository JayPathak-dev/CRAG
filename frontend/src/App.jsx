import { useState, useRef } from 'react';
import { Search, UploadCloud, File, FileText, CheckCircle, AlertTriangle, ArrowRight, X, Layers } from 'lucide-react';
import './index.css';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success'|'error'|'loading', message: '' }
  const fileInputRef = useRef(null);

  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // File Upload Handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = (newFiles) => {
    const pdfs = newFiles.filter(f => f.type === 'application/pdf' || f.name.endsWith('.pdf'));
    setFiles(prev => [...prev, ...pdfs]);
  };

  const removeFile = (indexToRemove) => {
    setFiles(files.filter((_, i) => i !== indexToRemove));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    
    setUploadStatus({ type: 'loading', message: 'Processing PDFs and generating embeddings...' });
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus({ type: 'success', message: data.message });
        setFiles([]); // Clear after success
      } else {
        throw new Error(data.detail || 'Failed to upload files');
      }
    } catch (err) {
      setUploadStatus({ type: 'error', message: err.message });
    }
  };

  // Query Handler
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setResults(null);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setResults(data);
      } else {
        throw new Error(data.detail || 'Search failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar for Uploads */}
      <aside className="sidebar">
        <div>
          <h2 className="gradient-text" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={28} />
            CRAG Engine
          </h2>
          <p className="info-text" style={{ marginTop: '8px' }}>
            Enterprise RAG with Critic self-correction and Hybrid Qdrant Search.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ marginBottom: '16px', fontSize: '1.1rem' }}>Data Ingestion</h3>
          
          <div 
            className="upload-zone"
            style={{ borderColor: isDragging ? 'var(--accent-primary)' : '' }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud size={40} color={isDragging ? 'var(--accent-primary)' : 'var(--text-secondary)'} />
            <div>
              <strong>Drag & drop PDFs</strong> or click to browse
            </div>
            <input 
              type="file" 
              multiple 
              accept=".pdf" 
              className="upload-input" 
              ref={fileInputRef}
              onChange={handleFileInput}
            />
          </div>

          {files.length > 0 && (
            <div className="file-list">
              {files.map((file, i) => (
                <div key={i} className="file-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <File size={16} color="var(--accent-primary)" />
                    <span style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {file.name}
                    </span>
                  </div>
                  <X size={16} style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => removeFile(i)} />
                </div>
              ))}
              <button 
                className="btn btn-primary" 
                style={{ width: '100%', marginTop: '12px' }}
                onClick={uploadFiles}
                disabled={uploadStatus?.type === 'loading'}
              >
                {uploadStatus?.type === 'loading' ? (
                  <><div className="loader loader-sm"></div> Indexing...</>
                ) : (
                  <>Index Documents <ArrowRight size={16} /></>
                )}
              </button>
            </div>
          )}

          {uploadStatus?.type === 'success' && (
            <div className="status-msg status-success fade-in">
              <CheckCircle size={16} style={{ marginBottom: '-3px', marginRight: '6px' }} />
              {uploadStatus.message}
            </div>
          )}
          {uploadStatus?.type === 'error' && (
            <div className="status-msg status-error fade-in">
              <AlertTriangle size={16} style={{ marginBottom: '-3px', marginRight: '6px' }} />
              {uploadStatus.message}
            </div>
          )}
        </div>
        
        <div style={{ marginTop: 'auto' }}>
          <div className="info-text" style={{ fontSize: '0.8rem' }}>
            <p><strong>Stack:</strong> React, FastAPI, Qdrant, Llama 3.2, LangGraph</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Ask your Enterprise Data</h1>
          <p className="info-text" style={{ fontSize: '1.1rem' }}>
            Hybrid search combined with an agentic critic to prevent hallucinations.
          </p>
        </header>

        <form onSubmit={handleSearch} className="search-container">
          <input 
            type="text" 
            className="search-input" 
            placeholder="e.g. What is the infrastructure failover protocol?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="search-btn" disabled={isSearching || !query.trim()}>
            {isSearching ? <div className="loader loader-sm"></div> : <Search size={20} />}
          </button>
        </form>

        {error && (
          <div className="status-msg status-error fade-in">
            {error}
          </div>
        )}

        {isSearching && !results && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '16px' }}>
            <div className="loader" style={{ width: '48px', height: '48px', borderWidth: '4px' }}></div>
            <p className="pulse gradient-text" style={{ fontWeight: 600, fontSize: '1.2rem' }}>
              Executing CRAG Workflow...
            </p>
            <p className="info-text">Running hybrid retrieval and critic agent validation</p>
          </div>
        )}

        {results && (
          <div className="results-grid fade-in">
            {/* Left Column: Retrieval */}
            <div>
              <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={20} className="gradient-text" /> 
                Retrieved Context
              </h3>
              
              {results.documents && results.documents.length > 0 ? (
                results.documents.map((doc, idx) => (
                  <div key={idx} className="chunk-card">
                    <div className="chunk-header">
                      <span className="badge badge-source">{doc.source || 'Unknown Source'}</span>
                      <span>Chunk #{doc.chunk_id} • {doc.category}</span>
                    </div>
                    <div style={{ fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                      {doc.text}
                    </div>
                  </div>
                ))
              ) : (
                <div className="chunk-card">
                  <p className="info-text">No relevant chunks found for this query.</p>
                </div>
              )}
            </div>

            {/* Right Column: Generation / Critic Action */}
            <div>
              <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={20} color="var(--success-color)" /> 
                Agent Output
              </h3>

              <div className="glass-panel">
                {results.generation ? (
                  <>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                      <span className="badge badge-success">Critic Passed</span>
                      <span className="badge" style={{ background: 'rgba(255,255,255,0.1)' }}>Grounded</span>
                    </div>
                    <div className="answer-card" style={{ borderRadius: 'var(--radius-md)' }}>
                      {results.generation}
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                      <span className="badge badge-error">Critic Rejected</span>
                      <span className="badge badge-warning">Query Rewritten</span>
                    </div>
                    <p className="info-text" style={{ marginBottom: '12px' }}>
                      The Critic Agent determined that the retrieved context did not contain enough information to answer the question reliably. To prevent hallucinations, the agent has rewritten your query:
                    </p>
                    <div className="answer-card" style={{ borderRadius: 'var(--radius-md)', borderColor: 'var(--warning-color)', background: 'rgba(245, 158, 11, 0.05)' }}>
                      <strong>Suggested Query:</strong> {results.transformed_query || 'N/A'}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
