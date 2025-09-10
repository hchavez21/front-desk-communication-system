import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { X, Search, Users, User, MessageCircle, Star } from 'lucide-react';

const NewConversationModal = ({ onClose, onConversationCreated }) => {
  const { user } = useAuth();
  const [step, setStep] = useState(1); // 1: Type selection, 2: Participant selection, 3: Details
  const [conversationType, setConversationType] = useState('direct');
  const [searchTerm, setSearchTerm] = useState('');
  const [availableUsers, setAvailableUsers] = useState([]);
  const [selectedParticipants, setSelectedParticipants] = useState([]);
  const [conversationTitle, setConversationTitle] = useState('');
  const [conversationDescription, setConversationDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchUsers = async (query) => {
    if (!query.trim()) {
      setAvailableUsers([]);
      return;
    }

    try {
      const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableUsers(data.users.filter(u => u.id !== user.id));
      }
    } catch (err) {
      console.error('Error searching users:', err);
    }
  };

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      searchUsers(searchTerm);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const handleParticipantToggle = (participant) => {
    setSelectedParticipants(prev => {
      const isSelected = prev.find(p => p.id === participant.id);
      if (isSelected) {
        return prev.filter(p => p.id !== participant.id);
      } else {
        // For direct conversations, only allow one other participant
        if (conversationType === 'direct') {
          return [participant];
        }
        return [...prev, participant];
      }
    });
  };

  const handleCreateConversation = async () => {
    if (selectedParticipants.length === 0) {
      setError('Please select at least one participant');
      return;
    }

    if (conversationType !== 'direct' && !conversationTitle.trim()) {
      setError('Please enter a conversation title');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const conversationData = {
        conversation_type: conversationType,
        participant_ids: selectedParticipants.map(p => p.id),
        title: conversationType === 'direct' ? null : conversationTitle.trim(),
        description: conversationDescription.trim() || null
      };

      const response = await fetch('/api/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(conversationData)
      });

      if (response.ok) {
        const data = await response.json();
        onConversationCreated(data.id);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create conversation');
      }
    } catch (err) {
      setError('Error creating conversation');
    } finally {
      setLoading(false);
    }
  };

  const conversationTypes = [
    {
      id: 'direct',
      name: 'Direct Message',
      description: 'Private conversation with one person',
      icon: <User className="w-6 h-6" />
    },
    {
      id: 'group',
      name: 'Group Chat',
      description: 'Conversation with multiple team members',
      icon: <Users className="w-6 h-6" />
    },
    {
      id: 'broadcast',
      name: 'Announcement',
      description: 'Send announcements to team members',
      icon: <Star className="w-6 h-6" />
    },
    {
      id: 'guest_related',
      name: 'Guest Discussion',
      description: 'Conversation about a specific guest',
      icon: <MessageCircle className="w-6 h-6" />
    }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {step === 1 && 'New Conversation'}
            {step === 2 && 'Select Participants'}
            {step === 3 && 'Conversation Details'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Step 1: Conversation Type Selection */}
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 mb-4">
                Choose the type of conversation you want to create:
              </p>
              
              <div className="space-y-3">
                {conversationTypes.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setConversationType(type.id)}
                    className={`w-full p-4 text-left border rounded-lg transition-colors ${
                      conversationType === type.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-lg ${
                        conversationType === type.id ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {type.icon}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{type.name}</h3>
                        <p className="text-sm text-gray-600">{type.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Participant Selection */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search for team members:
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search by name or email..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Selected Participants */}
              {selectedParticipants.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Selected ({selectedParticipants.length}):
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {selectedParticipants.map((participant) => (
                      <span
                        key={participant.id}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                      >
                        {participant.username}
                        <button
                          onClick={() => handleParticipantToggle(participant)}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Available Users */}
              {availableUsers.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Available team members:
                  </label>
                  <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg">
                    {availableUsers.map((availableUser) => {
                      const isSelected = selectedParticipants.find(p => p.id === availableUser.id);
                      return (
                        <button
                          key={availableUser.id}
                          onClick={() => handleParticipantToggle(availableUser)}
                          className={`w-full p-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                            isSelected ? 'bg-blue-50' : ''
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                              <span className="text-sm font-medium text-gray-600">
                                {availableUser.username.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{availableUser.username}</div>
                              <div className="text-sm text-gray-500">{availableUser.email}</div>
                            </div>
                            {isSelected && (
                              <div className="ml-auto text-blue-600">
                                ✓
                              </div>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {searchTerm && availableUsers.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  No users found matching "{searchTerm}"
                </p>
              )}
            </div>
          )}

          {/* Step 3: Conversation Details */}
          {step === 3 && conversationType !== 'direct' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Conversation Title *
                </label>
                <input
                  type="text"
                  value={conversationTitle}
                  onChange={(e) => setConversationTitle(e.target.value)}
                  placeholder="Enter conversation title..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={conversationDescription}
                  onChange={(e) => setConversationDescription(e.target.value)}
                  placeholder="Enter conversation description..."
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="bg-gray-50 p-3 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Summary:</h4>
                <p className="text-sm text-gray-600">
                  Creating a <strong>{conversationTypes.find(t => t.id === conversationType)?.name}</strong> with{' '}
                  <strong>{selectedParticipants.length}</strong> participant{selectedParticipants.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div className="flex space-x-2">
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
            )}
          </div>

          <div className="flex space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            
            {step < 3 || conversationType === 'direct' ? (
              <button
                onClick={() => {
                  if (step === 1) {
                    setStep(2);
                  } else if (step === 2) {
                    if (conversationType === 'direct') {
                      handleCreateConversation();
                    } else {
                      setStep(3);
                    }
                  }
                }}
                disabled={step === 2 && selectedParticipants.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {step === 2 && conversationType === 'direct' ? 'Create' : 'Next'}
              </button>
            ) : (
              <button
                onClick={handleCreateConversation}
                disabled={loading || !conversationTitle.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Creating...' : 'Create Conversation'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewConversationModal;

