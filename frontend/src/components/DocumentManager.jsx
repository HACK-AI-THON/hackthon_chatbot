import React, { useState } from 'react';
import axios from 'axios';

const DocumentManager = ({ documents, onDocumentsChange, loading, setLoading }) => {
  const [message, setMessage] = useState({ type: '', content: '' });
  const [scanning, setScanning] = useState(false);

  // Dynamically determine API base URL based on current host
  const getCurrentHost = () => {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      return `${protocol}//${hostname}:8000`;
    }
    return 'http://localhost:8000'; // fallback for SSR
  };
  
  const API_BASE_URL = getCurrentHost();

  const showMessage = (type, content) => {
    setMessage({ type, content });
    setTimeout(() => setMessage({ type: '', content: '' }), 5000);
  };

  const scanUploadsFolder = async () => {
    setScanning(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/scan-uploads`);
      
      const { processed_files, skipped_files, errors, total_chunks_added } = response.data;
      
      let message = '';
      if (processed_files.length > 0) {
        message += `✅ Processed ${processed_files.length} new documents. `;
      }
      if (skipped_files.length > 0) {
        message += `⏭️ Skipped ${skipped_files.length} existing documents. `;
      }
      if (errors.length > 0) {
        message += `❌ ${errors.length} errors occurred.`;
      }
      if (processed_files.length === 0 && skipped_files.length === 0 && errors.length === 0) {
        message = 'No new documents found in uploads folder.';
      }

      showMessage(errors.length > 0 ? 'error' : 'success', message || 'Scan completed successfully.');
      onDocumentsChange();
      
    } catch (error) {
      console.error('Scan error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to scan uploads folder. Please try again.';
      showMessage('error', errorMessage);
    } finally {
      setScanning(false);
    }
  };

  const refreshDocuments = () => {
    onDocumentsChange();
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (filename) => {
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'docx':
      case 'doc':
        return '📝';
      default:
        return '📄';
    }
  };

  return (
    <div className="document-manager">
      {/* Message Display */}
      {message.content && (
        <div className={`${message.type}-message`}>
          {message.content}
        </div>
      )}

      {/* Document Folder Info Section */}
      <div className="upload-section">
        <h3>📁 Document Management</h3>
        <p>Documents are automatically loaded from the uploads folder on server startup.</p>
        <p className="upload-info">
          Supported formats: PDF, Word (.pdf, .docx, .doc) • Place files in: <code>/uploads</code> folder
        </p>
        
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '20px' }}>
          <button 
            className="upload-button"
            onClick={scanUploadsFolder}
            disabled={scanning || loading}
          >
            {scanning ? '🔄 Scanning...' : '🔄 Scan for New Documents'}
          </button>
          
          <button 
            className="upload-button"
            onClick={refreshDocuments}
            disabled={loading || scanning}
            style={{ background: 'rgba(102, 126, 234, 0.8)' }}
          >
            🔄 Refresh List
          </button>
        </div>
      </div>

      {/* Documents List */}
      <div className="documents-list">
        <div className="documents-header">
          <h3>📚 Available Documents ({documents.length})</h3>
        </div>

        {documents.length === 0 ? (
          <div className="no-documents">
            <p>📝 No documents found in uploads folder.</p>
            <p>Place PDF or Word documents in the <code>/uploads</code> folder and restart the server or click "Scan for New Documents"!</p>
          </div>
        ) : (
          <div className="documents-grid">
            {documents.map((doc, index) => (
              <div key={index} className="document-item">
                <div className="document-info">
                  <div className="document-icon">
                    {getFileIcon(doc.filename)}
                  </div>
                  <div className="document-details">
                    <h4>{doc.filename}</h4>
                    <div className="document-stats">
                      <span className="stat">
                        📊 {doc.chunk_count} chunks
                      </span>
                      <span className="stat">
                        📏 {formatFileSize(doc.total_size)}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="document-actions">
                  <span className="document-status">
                    ✅ Loaded
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Upload Instructions */}
        {documents.length === 0 && (
          <div className="upload-instructions">
            <h4>💡 How to use:</h4>
            <ol>
              <li>Place PDF or Word documents in the <code>/uploads</code> folder on the server</li>
              <li>Restart the server or click "Scan for New Documents" to load them</li>
              <li>Go to the Chat tab once documents are loaded</li>
              <li>Ask questions about your document content</li>
              <li>Get AI-powered answers with source attribution</li>
            </ol>
            <div style={{ marginTop: '15px', padding: '10px', background: 'rgba(102, 126, 234, 0.1)', borderRadius: '8px' }}>
              <strong>📁 Folder Path:</strong> <code>C:\Users\vkk891\Hackthon_Chatbot\uploads\</code>
            </div>
          </div>
        )}
      </div>

      {(loading || scanning) && (
        <div className="loading-overlay">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>{scanning ? 'Scanning uploads folder...' : 'Loading documents...'}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManager;

