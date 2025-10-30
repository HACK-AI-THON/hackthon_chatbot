import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';
import { API_BASE_URL } from './config';

function App() {
  const [documents, setDocuments] = useState([]);

  // Fetch documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  return (
    <div className="app">
      <div className="app-container">
        <header className="app-header">
          <img 
            src="/hack-ai-thon.png" 
            alt="Hack-AI-Thon" 
            className="header-logo"
          />
          <p>Your Hack Assistant</p>
        </header>

        <main className="app-main">
          <ChatInterface 
            documents={documents}
            onDocumentsChange={fetchDocuments}
          />
        </main>

        <footer className="app-footer">
        
        </footer>
      </div>
    </div>
  );
}

export default App;

