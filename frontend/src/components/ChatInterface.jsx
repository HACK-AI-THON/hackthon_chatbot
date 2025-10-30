import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE_URL } from '../config';

const ChatInterface = ({ documents, onDocumentsChange }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [useOpenAI] = useState(true); // Always use Databricks LLM
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setLoading(true);

    // Add user message to chat
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }]);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: userMessage,
        use_openai: useOpenAI
      });

      // Add assistant response to chat
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }]);

    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message to chat
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your message. Please make sure the backend server is running and try again.',
        sources: [],
        timestamp: new Date(),
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getSuggestedQuestions = () => {
    if (!documents || documents.length === 0) {
      return [
        "Please upload some documents first to get started!",
        "Go to the Documents tab to upload PDF or Word files."
      ];
    }

    return [
      "Share me Hack-AI-Thon Registration link",
      "Show me Hack-AI-Thon schedule",
      "Show me Hack-AI-Thon location",
      "Show me Hack-AI-Thon contact information"      
    ];
  };

  return (
    <div className="chat-container">
      {/* Chat Messages */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>👋 Welcome to Hack-AI-Thon Assistant!</h3>
            <p>
              Ask me anything about the Hack-AI-Thon.
            </p>
            
            <div className="suggested-questions">
              <h4>💡 Try asking:</h4>
              <ul>
                {getSuggestedQuestions().map((question, index) => (
                  <li key={index}>
                    <button 
                      className="suggestion-button"
                      onClick={() => setInputValue(question)}
                      disabled={documents.length === 0 && index < 2}
                    >
                      {question}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-content">
                  {message.type === 'assistant' ? (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Custom styling for code blocks
                        code: ({node, inline, className, children, ...props}) => {
                          return inline ? (
                            <code className="inline-code" {...props}>{children}</code>
                          ) : (
                            <pre className="code-block">
                              <code className={className} {...props}>{children}</code>
                            </pre>
                          );
                        },
                        // Custom styling for tables
                        table: ({children}) => (
                          <div className="table-container">
                            <table>{children}</table>
                          </div>
                        ),
                        // Custom styling for blockquotes
                        blockquote: ({children}) => (
                          <blockquote className="markdown-blockquote">{children}</blockquote>
                        )
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    message.content
                  )}
                </div>
                
                <div className="message-timestamp">
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="message assistant loading">
                <div className="loading-indicator">
                  <span>AI is thinking</span>
                  <div className="loading-dots">
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <form onSubmit={handleSubmit} className="chat-input-container">
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            documents && documents.length > 0 
              ? "Ask me anything about your documents..." 
              : "Upload documents first, then ask questions..."
          }
          className="chat-input"
          disabled={loading}
          rows={1}
        />
        <button 
          type="submit" 
          className="send-button"
          disabled={!inputValue.trim() || loading || (documents && documents.length === 0)}
        >
          {loading ? '⏳' : '🚀'}
        </button>
      </form>

      {/* Chat Controls */}
      {messages.length > 0 && (
        <div className="chat-controls">
          <button onClick={clearChat} className="clear-chat-button">
            🗑️ Clear Chat
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;

