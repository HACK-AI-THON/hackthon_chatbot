import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [documents, setDocuments] = useState([]);

  // Fetch documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      // Dynamically determine API base URL based on current host
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      const apiBaseUrl = `${protocol}//${hostname}:8000`;
      
      const response = await fetch(`${apiBaseUrl}/documents`);
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

