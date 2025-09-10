import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const InteractionDetail = ({ interactionId }) => {
  const { user, token } = useAuth();
  const [interaction, setInteraction] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newComment, setNewComment] = useState('');
  const [addingComment, setAddingComment] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);

  // Priority level colors
  const priorityColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800'
  };

  // Status colors
  const statusColors = {
    open: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-purple-100 text-purple-800',
    resolved: 'bg-green-100 text-green-800',
    escalated: 'bg-red-100 text-red-800',
    closed: 'bg-gray-100 text-gray-800'
  };

  useEffect(() => {
    fetchInteraction();
    fetchComments();
  }, [interactionId]);

  const fetchInteraction = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/interactions/${interactionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setInteraction(data);
      } else {
        setError('Failed to fetch interaction details');
      }
    } catch (err) {
      setError('Error fetching interaction');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async () => {
    try {
      const response = await fetch(`/api/interactions/${interactionId}/comments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setComments(data);
      }
    } catch (err) {
      console.error('Error fetching comments:', err);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      setAddingComment(true);
      const response = await fetch(`/api/interactions/${interactionId}/comments`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ comment: newComment })
      });

      if (response.ok) {
        setNewComment('');
        fetchComments(); // Refresh comments
      } else {
        setError('Failed to add comment');
      }
    } catch (err) {
      setError('Error adding comment');
      console.error('Error:', err);
    } finally {
      setAddingComment(false);
    }
  };

  const handleQuickAction = async (action, data = {}) => {
    try {
      const response = await fetch(`/api/interactions/${interactionId}/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        fetchInteraction(); // Refresh interaction data
        fetchComments(); // Refresh comments (in case action added a comment)
      } else {
        setError(`Failed to ${action} interaction`);
      }
    } catch (err) {
      setError(`Error performing ${action}`);
      console.error('Error:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const canEdit = () => {
    if (!interaction || !user) return false;
    return user.role === 'manager' || 
           interaction.agent_id === user.id || 
           interaction.assigned_to === user.id;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error}
      </div>
    );
  }

  if (!interaction) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Interaction not found.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{interaction.subject}</h1>
          <p className="text-gray-600 mt-1">
            Interaction #{interaction.id} • Created {formatDate(interaction.created_at)}
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => window.location.href = '/interactions'}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Back to List
          </button>
          {canEdit() && (
            <button
              onClick={() => setShowEditForm(!showEditForm)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              {showEditForm ? 'Cancel Edit' : 'Edit'}
            </button>
          )}
        </div>
      </div>

      {/* Edit Form */}
      {showEditForm && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 mb-4">Edit mode - Use the form below to update this interaction.</p>
          {/* InteractionForm component would be imported and used here */}
          <div className="text-center py-8 text-gray-500">
            Edit form would be rendered here using the InteractionForm component
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Interaction Details</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Type</label>
                <p className="text-gray-900 capitalize">
                  {interaction.interaction_type.replace('-', ' ')}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Priority</label>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${priorityColors[interaction.priority_level]}`}>
                  {interaction.priority_level}
                </span>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Status</label>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[interaction.status]}`}>
                  {interaction.status.replace('_', ' ')}
                </span>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Location</label>
                <p className="text-gray-900">{interaction.location || 'N/A'}</p>
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-500 mb-2">Description</label>
              <p className="text-gray-900 whitespace-pre-wrap">{interaction.description}</p>
            </div>

            {interaction.resolution_notes && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <label className="block text-sm font-medium text-green-700 mb-2">Resolution Notes</label>
                <p className="text-green-900 whitespace-pre-wrap">{interaction.resolution_notes}</p>
              </div>
            )}
          </div>

          {/* Guest Information */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Guest Information</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Name</label>
                <p className="text-gray-900">
                  {interaction.guest_name || 
                   (interaction.guest ? `${interaction.guest.first_name} ${interaction.guest.last_name}` : 'N/A')}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Room Number</label>
                <p className="text-gray-900">{interaction.room_number || 'N/A'}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Phone</label>
                <p className="text-gray-900">{interaction.guest_phone || 'N/A'}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Email</label>
                <p className="text-gray-900">{interaction.guest_email || 'N/A'}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Reservation Number</label>
                <p className="text-gray-900">{interaction.reservation_number || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Tags */}
          {interaction.tags && interaction.tags.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {interaction.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            
            <div className="space-y-3">
              {interaction.status === 'open' && canEdit() && (
                <button
                  onClick={() => handleQuickAction('resolve')}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  Mark as Resolved
                </button>
              )}
              
              {interaction.status !== 'escalated' && user?.role === 'agent' && (
                <button
                  onClick={() => handleQuickAction('escalate', { escalation_reason: 'Requires management attention' })}
                  className="w-full px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
                >
                  Escalate to Management
                </button>
              )}
              
              {user?.role === 'manager' && (
                <button
                  onClick={() => {
                    const assignTo = prompt('Enter user ID to assign to:');
                    if (assignTo) {
                      handleQuickAction('assign', { assigned_to: parseInt(assignTo) });
                    }
                  }}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                >
                  Assign to Staff
                </button>
              )}
            </div>
          </div>

          {/* Assignment & Follow-up */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Assignment & Follow-up</h2>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-500">Agent</label>
                <p className="text-gray-900">
                  {interaction.agent ? 
                    `${interaction.agent.first_name} ${interaction.agent.last_name}` : 
                    'N/A'}
                </p>
              </div>
              
              {interaction.assigned_user && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Assigned To</label>
                  <p className="text-gray-900">
                    {`${interaction.assigned_user.first_name} ${interaction.assigned_user.last_name}`}
                  </p>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Follow-up Required</label>
                <p className="text-gray-900">{interaction.follow_up_required ? 'Yes' : 'No'}</p>
              </div>
              
              {interaction.follow_up_date && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Follow-up Date</label>
                  <p className="text-gray-900">{formatDate(interaction.follow_up_date)}</p>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-500">Manager Notification</label>
                <p className="text-gray-900">{interaction.manager_notification ? 'Yes' : 'No'}</p>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h2>
            
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium text-gray-900">Created:</span>
                <span className="text-gray-600 ml-2">{formatDate(interaction.created_at)}</span>
              </div>
              
              <div>
                <span className="font-medium text-gray-900">Last Updated:</span>
                <span className="text-gray-600 ml-2">{formatDate(interaction.updated_at)}</span>
              </div>
              
              {interaction.resolved_at && (
                <div>
                  <span className="font-medium text-gray-900">Resolved:</span>
                  <span className="text-gray-600 ml-2">{formatDate(interaction.resolved_at)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Comments Section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Comments & Updates</h2>
        
        {/* Add Comment Form */}
        <form onSubmit={handleAddComment} className="mb-6">
          <div className="flex space-x-3">
            <div className="flex-1">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment or update..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex-shrink-0">
              <button
                type="submit"
                disabled={addingComment || !newComment.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {addingComment ? 'Adding...' : 'Add Comment'}
              </button>
            </div>
          </div>
        </form>

        {/* Comments List */}
        <div className="space-y-4">
          {comments.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No comments yet.</p>
          ) : (
            comments.map((comment) => (
              <div key={comment.id} className="border-l-4 border-blue-200 pl-4 py-2">
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-gray-900">
                    {comment.user ? 
                      `${comment.user.first_name} ${comment.user.last_name}` : 
                      'Unknown User'}
                    <span className="text-sm text-gray-500 ml-2">
                      ({comment.user?.role})
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {formatDate(comment.created_at)}
                  </span>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap">{comment.comment}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default InteractionDetail;

