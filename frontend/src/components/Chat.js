import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import './Chat.css';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const { logout } = useAuth();

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get('/api/chat/conversations');
      setConversations(response.data.conversations);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const loadConversation = async (convId) => {
    try {
      const response = await axios.get(`/api/chat/conversation/${convId}`);
      setMessages(response.data.messages || []);
      setConversationId(convId);
      setSidebarOpen(false); // Close sidebar on mobile after selection
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);

    // Add user message to UI immediately
    const newUserMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await axios.post('/api/chat/send', {
        message: userMessage,
        conversation_id: conversationId
      });

      const { response: assistantResponse, conversation_id: newConvId } = response.data;

      // Update conversation ID if it's a new conversation
      if (!conversationId) {
        setConversationId(newConvId);
        fetchConversations(); // Refresh conversation list
      }

      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: assistantResponse,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setSidebarOpen(false);
  };

  const deleteConversation = async (convId) => {
    if (!window.confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      await axios.delete(`/api/chat/conversation/${convId}`);
      
      // If we're currently viewing this conversation, start a new one
      if (convId === conversationId) {
        startNewConversation();
      }
      
      // Refresh conversation list
      fetchConversations();
    } catch (error) {
      console.error('Error deleting conversation:', error);
      alert('Failed to delete conversation. Please try again.');
    }
  };

  return (
    <div className="chat-container">
      {/* Sidebar */}
      <div className={`chat-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>Conversations</h3>
          <button onClick={startNewConversation} className="new-chat-btn">
            <span>+</span> New Chat
          </button>
        </div>
        
        <div className="conversations-list">
          {conversations.map((conv) => (
            <div
              key={conv.conversation_id}
              className={`conversation-item ${
                conv.conversation_id === conversationId ? 'active' : ''
              }`}
            >
              <div 
                className="conversation-content"
                onClick={() => loadConversation(conv.conversation_id)}
              >
                <div className="conversation-preview">
                  {conv.preview}
                </div>
                <div className="conversation-meta">
                  <span className="conversation-date">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </span>
                  <span className="message-count">
                    {conv.message_count} messages
                  </span>
                </div>
              </div>
              <button
                className="delete-conversation-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(conv.conversation_id);
                }}
                title="Delete conversation"
              >
                ×
              </button>
            </div>
          ))}
          
          {conversations.length === 0 && (
            <div className="no-conversations">
              <p>No conversations yet.</p>
              <p>Start a new chat to begin!</p>
            </div>
          )}
        </div>
        
        <div className="sidebar-footer">
          <button onClick={logout} className="logout-btn">
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        <div className="chat-header">
          <button 
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
          <h2>Organization Chat Assistant</h2>
          <div className="header-actions">
            <span className="status-indicator online">Online</span>
          </div>
        </div>

        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon">🤖</div>
              <h3>Welcome to Organization Chat!</h3>
              <p>I'm your AI assistant. Ask me anything and I'll help you with information and tasks.</p>
              <div className="welcome-suggestions">
                <button 
                  onClick={() => setInput("What can you help me with?")}
                  className="suggestion-btn"
                >
                  What can you help me with?
                </button>
                <button 
                  onClick={() => setInput("Tell me about this organization.")}
                  className="suggestion-btn"
                >
                  Tell me about this organization
                </button>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.role} ${message.isError ? 'error' : ''}`}
              >
                <div className="message-avatar">
                  {message.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.content}
                  </div>
                  <div className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={sendMessage} className="chat-input-form">
          <div className="input-container">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
              className="chat-input"
              maxLength={4000}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="send-button"
            >
              {loading ? (
                <div className="loading-spinner"></div>
              ) : (
                <span>→</span>
              )}
            </button>
          </div>
          <div className="input-footer">
            <span className="char-count">
              {input.length}/4000
            </span>
          </div>
        </form>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}

export default Chat;
