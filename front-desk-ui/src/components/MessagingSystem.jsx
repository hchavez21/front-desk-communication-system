import React, { useState } from 'react';
import ConversationList from './ConversationList';
import MessageView from './MessageView';
import NewConversationModal from './NewConversationModal';

const MessagingSystem = () => {
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [showNewConversationModal, setShowNewConversationModal] = useState(false);

  const handleSelectConversation = (conversationId) => {
    setSelectedConversationId(conversationId);
  };

  const handleNewConversation = () => {
    setShowNewConversationModal(true);
  };

  const handleConversationCreated = (conversationId) => {
    setShowNewConversationModal(false);
    setSelectedConversationId(conversationId);
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar - Conversation List */}
      <div className="w-80 bg-white border-r border-gray-200 flex-shrink-0">
        <ConversationList
          selectedConversationId={selectedConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </div>

      {/* Main Content - Message View */}
      <div className="flex-1 flex flex-col">
        <MessageView conversationId={selectedConversationId} />
      </div>

      {/* New Conversation Modal */}
      {showNewConversationModal && (
        <NewConversationModal
          onClose={() => setShowNewConversationModal(false)}
          onConversationCreated={handleConversationCreated}
        />
      )}
    </div>
  );
};

export default MessagingSystem;

