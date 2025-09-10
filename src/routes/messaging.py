from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.user import db, User
from src.models.conversation import Conversation, ConversationParticipant, ConversationMessage, MessageReaction
from src.models.guest import Guest
from datetime import datetime
from sqlalchemy import or_, and_

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get all conversations for the current user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get conversations where user is a participant
        conversations_query = db.session.query(Conversation).join(ConversationParticipant).filter(
            ConversationParticipant.user_id == current_user.id,
            Conversation.is_archived == False
        ).order_by(Conversation.updated_at.desc())
        
        conversations = conversations_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'conversations': [conv.to_dict(current_user.id) for conv in conversations.items],
            'total': conversations.total,
            'pages': conversations.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': conversations.has_next,
            'has_prev': conversations.has_prev
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        conversation_type = data.get('conversation_type', 'direct')
        participant_ids = data.get('participant_ids', [])
        
        if not participant_ids:
            return jsonify({'error': 'At least one participant is required'}), 400
        
        # Ensure current user is included in participants
        if current_user.id not in participant_ids:
            participant_ids.append(current_user.id)
        
        # For direct conversations, check if one already exists
        if conversation_type == 'direct' and len(participant_ids) == 2:
            existing_conv = db.session.query(Conversation).join(ConversationParticipant).filter(
                Conversation.conversation_type == 'direct'
            ).group_by(Conversation.id).having(
                db.func.count(ConversationParticipant.user_id) == 2
            ).all()
            
            for conv in existing_conv:
                conv_participants = [p.user_id for p in conv.participants]
                if set(conv_participants) == set(participant_ids):
                    return jsonify(conv.to_dict(current_user.id))
        
        # Create new conversation
        conversation = Conversation(
            title=data.get('title'),
            description=data.get('description'),
            conversation_type=conversation_type,
            guest_id=data.get('guest_id'),
            created_by=current_user.id
        )
        
        db.session.add(conversation)
        db.session.flush()  # Get the conversation ID
        
        # Add participants
        for user_id in participant_ids:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=user_id,
                role='admin' if user_id == current_user.id else 'member'
            )
            db.session.add(participant)
        
        db.session.commit()
        
        return jsonify(conversation.to_dict(current_user.id)), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_conversation(conversation_id):
    """Get a specific conversation"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Check if user is a participant
        if not conversation.has_participant(current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(conversation.to_dict(current_user.id))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_messages(conversation_id):
    """Get messages for a conversation"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Check if user is a participant
        if not conversation.has_participant(current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        messages = ConversationMessage.query.filter_by(
            conversation_id=conversation_id,
            is_deleted=False
        ).order_by(ConversationMessage.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Mark messages as read
        participant = ConversationParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if participant:
            participant.last_read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'messages': [msg.to_dict() for msg in reversed(messages.items)],
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': messages.has_next,
            'has_prev': messages.has_prev
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message():
    """Send a message to a conversation"""
    try:
        conversation_id = request.view_args['conversation_id']
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Check if user is a participant
        if not conversation.has_participant(current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if conversation is locked
        if conversation.is_locked:
            return jsonify({'error': 'This conversation is locked'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('content') and not data.get('file_url'):
            return jsonify({'error': 'Message content or file is required'}), 400
        
        # Create message
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            message_type=data.get('message_type', 'text'),
            content=data.get('content'),
            file_url=data.get('file_url'),
            file_name=data.get('file_name'),
            file_size=data.get('file_size'),
            is_priority=data.get('is_priority', False),
            reply_to_message_id=data.get('reply_to_message_id')
        )
        
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(message.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/messages/<int:message_id>', methods=['PUT'])
@login_required
def edit_message(message_id):
    """Edit a message"""
    try:
        message = ConversationMessage.query.get_or_404(message_id)
        
        # Check if user is the sender
        if message.sender_id != current_user.id:
            return jsonify({'error': 'You can only edit your own messages'}), 403
        
        data = request.get_json()
        
        # Update message content
        message.content = data.get('content', message.content)
        message.is_edited = True
        message.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(message.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    try:
        message = ConversationMessage.query.get_or_404(message_id)
        
        # Check if user is the sender or has admin role
        participant = ConversationParticipant.query.filter_by(
            conversation_id=message.conversation_id,
            user_id=current_user.id
        ).first()
        
        if message.sender_id != current_user.id and (not participant or participant.role != 'admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Soft delete
        message.is_deleted = True
        message.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Message deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/messages/<int:message_id>/reactions', methods=['POST'])
@login_required
def add_reaction(message_id):
    """Add a reaction to a message"""
    try:
        message = ConversationMessage.query.get_or_404(message_id)
        
        # Check if user has access to the conversation
        if not message.conversation.has_participant(current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        reaction_type = data.get('reaction_type')
        
        if not reaction_type:
            return jsonify({'error': 'Reaction type is required'}), 400
        
        # Check if reaction already exists
        existing_reaction = MessageReaction.query.filter_by(
            message_id=message_id,
            user_id=current_user.id,
            reaction_type=reaction_type
        ).first()
        
        if existing_reaction:
            # Remove existing reaction (toggle)
            db.session.delete(existing_reaction)
            db.session.commit()
            return jsonify({'message': 'Reaction removed'})
        
        # Add new reaction
        reaction = MessageReaction(
            message_id=message_id,
            user_id=current_user.id,
            reaction_type=reaction_type
        )
        
        db.session.add(reaction)
        db.session.commit()
        
        return jsonify(reaction.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations/<int:conversation_id>/participants', methods=['POST'])
@login_required
def add_participant(conversation_id):
    """Add a participant to a conversation"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Check if user has admin role in conversation
        participant = ConversationParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not participant or participant.role != 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Check if user exists
        user = User.query.get_or_404(user_id)
        
        # Check if user is already a participant
        existing_participant = ConversationParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id
        ).first()
        
        if existing_participant:
            return jsonify({'error': 'User is already a participant'}), 400
        
        # Add participant
        new_participant = ConversationParticipant(
            conversation_id=conversation_id,
            user_id=user_id,
            role=data.get('role', 'member')
        )
        
        db.session.add(new_participant)
        db.session.commit()
        
        return jsonify(new_participant.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations/<int:conversation_id>/participants/<int:user_id>', methods=['DELETE'])
@login_required
def remove_participant(conversation_id, user_id):
    """Remove a participant from a conversation"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Check if user has admin role in conversation or is removing themselves
        participant = ConversationParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not participant or (participant.role != 'admin' and current_user.id != user_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Find participant to remove
        target_participant = ConversationParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id
        ).first()
        
        if not target_participant:
            return jsonify({'error': 'Participant not found'}), 404
        
        db.session.delete(target_participant)
        db.session.commit()
        
        return jsonify({'message': 'Participant removed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """Search for users to add to conversations"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'users': []})
        
        users = User.query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        return jsonify({
            'users': [user.to_dict() for user in users]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/conversations/<int:conversation_id>/mark-read', methods=['POST'])
@login_required
def mark_conversation_read(conversation_id):
    """Mark all messages in a conversation as read"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Check if user is a participant
        if not conversation.has_participant(current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        participant = ConversationParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if participant:
            participant.last_read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'message': 'Conversation marked as read'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/messaging/stats', methods=['GET'])
@login_required
def get_messaging_stats():
    """Get messaging statistics for the current user"""
    try:
        # Total conversations
        total_conversations = db.session.query(Conversation).join(ConversationParticipant).filter(
            ConversationParticipant.user_id == current_user.id
        ).count()
        
        # Unread conversations
        unread_conversations = 0
        user_conversations = db.session.query(Conversation).join(ConversationParticipant).filter(
            ConversationParticipant.user_id == current_user.id
        ).all()
        
        for conv in user_conversations:
            if conv.get_unread_count(current_user.id) > 0:
                unread_conversations += 1
        
        # Messages sent today
        from datetime import date
        today = date.today()
        messages_today = ConversationMessage.query.filter(
            ConversationMessage.sender_id == current_user.id,
            db.func.date(ConversationMessage.created_at) == today
        ).count()
        
        return jsonify({
            'total_conversations': total_conversations,
            'unread_conversations': unread_conversations,
            'messages_today': messages_today
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

