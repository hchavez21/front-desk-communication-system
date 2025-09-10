from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.models.user import db, User
from src.models.message import Message

message_bp = Blueprint('message', __name__)

@message_bp.route('/messages', methods=['GET'])
@login_required
def get_messages():
    # Get query parameters
    message_type = request.args.get('type', 'all')  # 'sent', 'received', 'announcements', 'all'
    
    if message_type == 'sent':
        messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    elif message_type == 'received':
        messages = Message.query.filter(
            (Message.recipient_id == current_user.id) | 
            (Message.is_announcement == True)
        ).order_by(Message.created_at.desc()).all()
    elif message_type == 'announcements':
        messages = Message.query.filter_by(is_announcement=True).order_by(Message.created_at.desc()).all()
    else:  # all
        messages = Message.query.filter(
            (Message.sender_id == current_user.id) |
            (Message.recipient_id == current_user.id) |
            (Message.is_announcement == True)
        ).order_by(Message.created_at.desc()).all()
    
    return jsonify([message.to_dict() for message in messages])

@message_bp.route('/messages', methods=['POST'])
@login_required
def create_message():
    data = request.json
    
    # Validate required fields
    if not data.get('subject') or not data.get('content'):
        return jsonify({'error': 'Subject and content are required'}), 400
    
    is_announcement = data.get('is_announcement', False)
    
    # Only managers can send announcements
    if is_announcement and current_user.role != 'manager':
        return jsonify({'error': 'Only managers can send announcements'}), 403
    
    # For non-announcements, recipient is required
    recipient_id = None
    if not is_announcement:
        recipient_id = data.get('recipient_id')
        if not recipient_id:
            return jsonify({'error': 'recipient_id is required for non-announcements'}), 400
        
        # Check if recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        subject=data['subject'],
        content=data['content'],
        is_announcement=is_announcement
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify(message.to_dict()), 201

@message_bp.route('/messages/<int:message_id>', methods=['GET'])
@login_required
def get_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Check permissions
    can_view = (
        message.sender_id == current_user.id or
        message.recipient_id == current_user.id or
        message.is_announcement
    )
    
    if not can_view:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(message.to_dict())

@message_bp.route('/messages/<int:message_id>/read', methods=['PUT'])
@login_required
def mark_message_read(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Only recipient can mark message as read
    if message.recipient_id != current_user.id and not message.is_announcement:
        return jsonify({'error': 'Access denied'}), 403
    
    message.is_read = True
    db.session.commit()
    
    return jsonify(message.to_dict())

@message_bp.route('/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Only sender or managers can delete messages
    if message.sender_id != current_user.id and current_user.role != 'manager':
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(message)
    db.session.commit()
    
    return '', 204

@message_bp.route('/messages/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    count = Message.query.filter(
        ((Message.recipient_id == current_user.id) | (Message.is_announcement == True)) &
        (Message.is_read == False)
    ).count()
    
    return jsonify({'unread_count': count})

