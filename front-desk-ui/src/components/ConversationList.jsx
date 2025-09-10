import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MessageCircle, Plus, Search, Users, User, Star, Clock, Archive } from 'lucide-react';

const ConversationList = ({ selectedConversationId, onSelectConversation, onNewConversation }) => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/conversations', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations);
      } else {
        setError('Failed to fetch conversations');
      }
    } catch (err) {
      setError('Error loading conversations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
    
    // Poll for new messages every 30 seconds
    const interval = setInterval(fetchConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  const filteredConversations = conversations.filter(conv => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      conv.title?.toLowerCase().includes(searchLower) ||
      conv.participants.some(p => 
        p.username?.toLowerCase().includes(searchLower) ||
        p.email?.toLowerCase().includes(searchLower)
      ) ||
      conv.last_message?.content?.toLowerCase().includes(searchLower)
    );
  });

  const getConversationIcon = (conversation) => {
    switch (conversation.conversation_type) {
      case 'group':
        return <Users className="w-4 h-4" />;
      case 'broadcast':
        return <Star className="w-4 h-4" />;
      case 'guest_related':
        return <User className="w-4 h-4 text-blue-600" />;
      default:
        return <MessageCircle className="w-4 h-4" />;
    }
  };

  const getConversationTitle = (conversation) => {
    if (conversation.title) {
      return conversation.title;
    }

    if (conversation.conversation_type === 'direct') {
      const otherParticipant = conversation.participants.find(p => p.id !== user.id);
      return otherParticipant ? otherParticipant.username : 'Unknown User';
    }

    if (conversation.conversation_type === 'guest_related' && conversation.guest) {
      return `Guest: ${conversation.guest.full_name}`;
    }

    return `${conversation.conversation_type.charAt(0).toUpperCase() + conversation.conversation_type.slice(1)} Chat`;
  };

  const formatLastMessageTime = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      const diffInMinutes = Math.floor((now - date) / (1000 * 60));
      return diffInMinutes < 1 ? 'Just now' : `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const truncateMessage = (message, maxLength = 50) => {
    if (!message) return '';
    return message.length > maxLength ? message.substring(0, maxLength) + '...' : message;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Messages</h2>
          <button
            onClick={onNewConversation}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="New Conversation"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="p-4 text-red-600 text-sm">
            {error}
          </div>
        )}

        {filteredConversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <MessageCircle className="mx-auto h-8 w-8 text-gray-400 mb-2" />
            <p className="text-sm">
              {searchTerm ? 'No conversations found' : 'No conversations yet'}
            </p>
            {!searchTerm && (
              <button
                onClick={onNewConversation}
                className="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Start a conversation
              </button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onSelectConversation(conversation.id)}
                className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                  selectedConversationId === conversation.id ? 'bg-blue-50 border-r-2 border-blue-600' : ''
                }`}
              >
                <div className="flex items-start space-x-3">
                  {/* Avatar/Icon */}
                  <div className="flex-shrink-0">
                    {conversation.conversation_type === 'direct' ? (
                      <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {(() => {
                            const otherParticipant = conversation.participants.find(p => p.id !== user.id);
                            return otherParticipant ? 
                              otherParticipant.username.charAt(0).toUpperCase() : 
                              '?';
                          })()}
                        </span>
                      </div>
                    ) : (
                      <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        {getConversationIcon(conversation)}
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {getConversationTitle(conversation)}
                      </h3>
                      <div className="flex items-center space-x-1">
                        {conversation.unread_count > 0 && (
                          <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-blue-600 rounded-full">
                            {conversation.unread_count > 99 ? '99+' : conversation.unread_count}
                          </span>
                        )}
                        {conversation.last_message && (
                          <span className="text-xs text-gray-500 flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {formatLastMessageTime(conversation.last_message.created_at)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Last Message */}
                    {conversation.last_message && (
                      <div className="mt-1">
                        <p className="text-sm text-gray-600">
                          <span className="font-medium">
                            {conversation.last_message.sender.id === user.id ? 'You' : conversation.last_message.sender.username}:
                          </span>
                          {' '}
                          {conversation.last_message.message_type === 'file' ? (
                            <span className="italic">sent a file</span>
                          ) : (
                            truncateMessage(conversation.last_message.content)
                          )}
                        </p>
                      </div>
                    )}

                    {/* Conversation Info */}
                    <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                      {conversation.conversation_type !== 'direct' && (
                        <span className="flex items-center">
                          <Users className="w-3 h-3 mr-1" />
                          {conversation.participant_count} members
                        </span>
                      )}
                      {conversation.guest && (
                        <span className="flex items-center text-blue-600">
                          <User className="w-3 h-3 mr-1" />
                          Guest conversation
                        </span>
                      )}
                      {conversation.is_pinned && (
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                      )}
                      {conversation.is_archived && (
                        <Archive className="w-3 h-3 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationList;

