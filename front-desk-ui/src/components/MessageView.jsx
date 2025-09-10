import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Send, Paperclip, Smile, MoreVertical, Reply, Edit, Trash, Heart, ThumbsUp, Laugh } from 'lucide-react';

const MessageView = ({ conversationId }) => {
  const { user } = useAuth();
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [replyTo, setReplyTo] = useState(null);
  const [editingMessage, setEditingMessage] = useState(null);
  const messagesEndRef = useRef(null);
  const messageInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversation = async () => {
    try {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setConversation(data);
      } else {
        setError('Failed to fetch conversation');
      }
    } catch (err) {
      setError('Error loading conversation');
    }
  };

  const fetchMessages = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/conversations/${conversationId}/messages`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages);
        
        // Mark conversation as read
        await fetch(`/api/conversations/${conversationId}/mark-read`, {
          method: 'POST',
          credentials: 'include'
        });
      } else {
        setError('Failed to fetch messages');
      }
    } catch (err) {
      setError('Error loading messages');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (conversationId) {
      fetchConversation();
      fetchMessages();
    }
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Poll for new messages every 10 seconds
    if (conversationId) {
      const interval = setInterval(fetchMessages, 10000);
      return () => clearInterval(interval);
    }
  }, [conversationId]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const messageData = {
        content: newMessage.trim(),
        message_type: 'text',
        reply_to_message_id: replyTo?.id || null
      };

      const response = await fetch(`/api/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(messageData)
      });

      if (response.ok) {
        setNewMessage('');
        setReplyTo(null);
        fetchMessages(); // Refresh messages
      } else {
        setError('Failed to send message');
      }
    } catch (err) {
      setError('Error sending message');
    } finally {
      setSending(false);
    }
  };

  const handleEditMessage = async (messageId, newContent) => {
    try {
      const response = await fetch(`/api/messages/${messageId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ content: newContent })
      });

      if (response.ok) {
        setEditingMessage(null);
        fetchMessages();
      } else {
        setError('Failed to edit message');
      }
    } catch (err) {
      setError('Error editing message');
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!confirm('Are you sure you want to delete this message?')) return;

    try {
      const response = await fetch(`/api/messages/${messageId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        fetchMessages();
      } else {
        setError('Failed to delete message');
      }
    } catch (err) {
      setError('Error deleting message');
    }
  };

  const handleReaction = async (messageId, reactionType) => {
    try {
      const response = await fetch(`/api/messages/${messageId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ reaction_type: reactionType })
      });

      if (response.ok) {
        fetchMessages();
      }
    } catch (err) {
      console.error('Error adding reaction:', err);
    }
  };

  const formatMessageTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  };

  const getReactionIcon = (type) => {
    switch (type) {
      case 'like':
        return <ThumbsUp className="w-4 h-4" />;
      case 'love':
        return <Heart className="w-4 h-4" />;
      case 'laugh':
        return <Laugh className="w-4 h-4" />;
      default:
        return <ThumbsUp className="w-4 h-4" />;
    }
  };

  if (!conversationId) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <MessageCircle className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Select a conversation</h3>
          <p className="text-gray-500">Choose a conversation from the sidebar to start messaging</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      {conversation && (
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {conversation.title || `${conversation.conversation_type} Chat`}
              </h2>
              <p className="text-sm text-gray-500">
                {conversation.participant_count} participants
                {conversation.guest && ` • Guest: ${conversation.guest.full_name}`}
              </p>
            </div>
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender.id === user.id ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-xs lg:max-w-md ${message.sender.id === user.id ? 'order-2' : 'order-1'}`}>
              {/* Reply indicator */}
              {message.reply_to && (
                <div className="mb-1 text-xs text-gray-500 px-3">
                  Replying to {message.reply_to.sender.username}
                </div>
              )}

              <div
                className={`px-4 py-2 rounded-lg ${
                  message.sender.id === user.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {/* Sender name for group conversations */}
                {conversation?.conversation_type !== 'direct' && message.sender.id !== user.id && (
                  <div className="text-xs font-medium mb-1 opacity-75">
                    {message.sender.username}
                  </div>
                )}

                {/* Message content */}
                {editingMessage === message.id ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const newContent = e.target.content.value;
                      handleEditMessage(message.id, newContent);
                    }}
                    className="space-y-2"
                  >
                    <input
                      name="content"
                      defaultValue={message.content}
                      className="w-full px-2 py-1 text-sm border rounded text-gray-900"
                      autoFocus
                    />
                    <div className="flex space-x-2">
                      <button
                        type="submit"
                        className="text-xs px-2 py-1 bg-blue-600 text-white rounded"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingMessage(null)}
                        className="text-xs px-2 py-1 bg-gray-300 text-gray-700 rounded"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <div>
                    <p className="text-sm">{message.content}</p>
                    {message.is_edited && (
                      <span className="text-xs opacity-75">(edited)</span>
                    )}
                  </div>
                )}

                {/* Message reactions */}
                {message.reactions && message.reactions.length > 0 && (
                  <div className="flex space-x-1 mt-2">
                    {message.reactions.map((reaction) => (
                      <button
                        key={reaction.id}
                        onClick={() => handleReaction(message.id, reaction.reaction_type)}
                        className="flex items-center space-x-1 px-2 py-1 bg-white bg-opacity-20 rounded-full text-xs"
                      >
                        {getReactionIcon(reaction.reaction_type)}
                        <span>{reaction.count}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Message actions */}
              <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                <span>{formatMessageTime(message.created_at)}</span>
                
                {/* Action buttons */}
                <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => setReplyTo(message)}
                    className="p-1 hover:bg-gray-200 rounded"
                    title="Reply"
                  >
                    <Reply className="w-3 h-3" />
                  </button>
                  
                  <button
                    onClick={() => handleReaction(message.id, 'like')}
                    className="p-1 hover:bg-gray-200 rounded"
                    title="Like"
                  >
                    <ThumbsUp className="w-3 h-3" />
                  </button>

                  {message.sender.id === user.id && (
                    <>
                      <button
                        onClick={() => setEditingMessage(message.id)}
                        className="p-1 hover:bg-gray-200 rounded"
                        title="Edit"
                      >
                        <Edit className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleDeleteMessage(message.id)}
                        className="p-1 hover:bg-gray-200 rounded text-red-600"
                        title="Delete"
                      >
                        <Trash className="w-3 h-3" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Reply indicator */}
      {replyTo && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Replying to <span className="font-medium">{replyTo.sender.username}</span>: {replyTo.content.substring(0, 50)}...
            </div>
            <button
              onClick={() => setReplyTo(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSendMessage} className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              ref={messageInputRef}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="1"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
            />
          </div>
          
          <div className="flex space-x-1">
            <button
              type="button"
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
              title="Attach file"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            
            <button
              type="button"
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
              title="Add emoji"
            >
              <Smile className="w-5 h-5" />
            </button>
            
            <button
              type="submit"
              disabled={!newMessage.trim() || sending}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MessageView;

