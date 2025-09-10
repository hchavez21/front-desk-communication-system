from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from src.models.user import db, User
from src.models.interaction import Interaction, InteractionComment, InteractionAttachment
from src.models.guest import Guest
from datetime import datetime
import os
import uuid

interaction_bp = Blueprint('interaction', __name__)

# Configuration for file uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@interaction_bp.route('/interactions', methods=['GET'])
@login_required
def get_interactions():
    # Get query parameters for filtering and pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    interaction_type = request.args.get('type')
    status = request.args.get('status')
    priority_level = request.args.get('priority')
    agent_id = request.args.get('agent_id')
    guest_id = request.args.get('guest_id')
    search = request.args.get('search')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Interaction.query
    
    # Apply filters
    if interaction_type:
        query = query.filter(Interaction.interaction_type == interaction_type)
    if status:
        query = query.filter(Interaction.status == status)
    if priority_level:
        query = query.filter(Interaction.priority_level == priority_level)
    if agent_id:
        query = query.filter(Interaction.agent_id == agent_id)
    if guest_id:
        query = query.filter(Interaction.guest_id == guest_id)
    
    # Search functionality
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Interaction.subject.ilike(search_term),
                Interaction.description.ilike(search_term),
                Interaction.guest_name.ilike(search_term),
                Interaction.room_number.ilike(search_term),
                Interaction.tags.ilike(search_term)
            )
        )
    
    # Date range filtering
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(Interaction.created_at >= date_from_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format'}), 400
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(Interaction.created_at <= date_to_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format'}), 400
    
    # If user is an agent, only show their interactions unless they're a manager
    if current_user.role == 'agent':
        query = query.filter(Interaction.agent_id == current_user.id)
    
    # Pagination
    interactions = query.order_by(Interaction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'interactions': [interaction.to_dict() for interaction in interactions.items],
        'total': interactions.total,
        'pages': interactions.pages,
        'current_page': page,
        'per_page': per_page
    })

@interaction_bp.route('/interactions', methods=['POST'])
@login_required
def create_interaction():
    data = request.json
    
    # Validate required fields
    required_fields = ['interaction_type', 'subject', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate interaction type
    if data['interaction_type'] not in Interaction.get_interaction_types():
        return jsonify({'error': f'interaction_type must be one of: {", ".join(Interaction.get_interaction_types())}'}), 400
    
    # Validate priority level
    priority_level = data.get('priority_level', 'medium')
    if priority_level not in Interaction.get_priority_levels():
        return jsonify({'error': f'priority_level must be one of: {", ".join(Interaction.get_priority_levels())}'}), 400
    
    # Validate status
    status = data.get('status', 'open')
    if status not in Interaction.get_status_options():
        return jsonify({'error': f'status must be one of: {", ".join(Interaction.get_status_options())}'}), 400
    
    # Check if guest exists (if guest_id provided)
    guest = None
    if data.get('guest_id'):
        guest = Guest.query.get(data['guest_id'])
        if not guest:
            return jsonify({'error': 'Guest not found'}), 404
    
    # Validate assigned_to user (if provided)
    assigned_user = None
    if data.get('assigned_to'):
        assigned_user = User.query.get(data['assigned_to'])
        if not assigned_user:
            return jsonify({'error': 'Assigned user not found'}), 404
    
    # Parse follow_up_date if provided
    follow_up_date = None
    if data.get('follow_up_date'):
        try:
            follow_up_date = datetime.fromisoformat(data['follow_up_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid follow_up_date format'}), 400
    
    # Process tags
    tags = None
    if data.get('tags') and isinstance(data['tags'], list):
        tags = ','.join([tag.strip() for tag in data['tags'] if tag.strip()])
    
    interaction = Interaction(
        guest_id=data.get('guest_id'),
        agent_id=current_user.id,
        interaction_type=data['interaction_type'],
        priority_level=priority_level,
        status=status,
        subject=data['subject'],
        description=data['description'],
        location=data.get('location'),
        guest_name=data.get('guest_name'),
        room_number=data.get('room_number'),
        guest_phone=data.get('guest_phone'),
        guest_email=data.get('guest_email'),
        reservation_number=data.get('reservation_number'),
        follow_up_required=data.get('follow_up_required', False),
        follow_up_date=follow_up_date,
        assigned_to=data.get('assigned_to'),
        manager_notification=data.get('manager_notification', False),
        resolution_notes=data.get('resolution_notes'),
        tags=tags
    )
    
    db.session.add(interaction)
    db.session.commit()
    
    return jsonify(interaction.to_dict()), 201

@interaction_bp.route('/interactions/<int:interaction_id>', methods=['GET'])
@login_required
def get_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Check permissions - agents can only view their own interactions or assigned ones
    if current_user.role == 'agent' and interaction.agent_id != current_user.id and interaction.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(interaction.to_dict(include_comments=True, include_attachments=True))

@interaction_bp.route('/interactions/<int:interaction_id>', methods=['PUT'])
@login_required
def update_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Check permissions - agents can only update their own interactions or assigned ones
    if current_user.role == 'agent' and interaction.agent_id != current_user.id and interaction.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    
    # Update fields with validation
    if 'interaction_type' in data:
        if data['interaction_type'] not in Interaction.get_interaction_types():
            return jsonify({'error': f'interaction_type must be one of: {", ".join(Interaction.get_interaction_types())}'}), 400
        interaction.interaction_type = data['interaction_type']
    
    if 'priority_level' in data:
        if data['priority_level'] not in Interaction.get_priority_levels():
            return jsonify({'error': f'priority_level must be one of: {", ".join(Interaction.get_priority_levels())}'}), 400
        interaction.priority_level = data['priority_level']
    
    if 'status' in data:
        if data['status'] not in Interaction.get_status_options():
            return jsonify({'error': f'status must be one of: {", ".join(Interaction.get_status_options())}'}), 400
        interaction.status = data['status']
        
        # Set resolved_at timestamp when status changes to resolved or closed
        if data['status'] in ['resolved', 'closed'] and not interaction.resolved_at:
            interaction.resolved_at = datetime.utcnow()
    
    # Update other fields
    for field in ['subject', 'description', 'location', 'guest_name', 'room_number', 
                  'guest_phone', 'guest_email', 'reservation_number', 'resolution_notes']:
        if field in data:
            setattr(interaction, field, data[field])
    
    # Update boolean fields
    for field in ['follow_up_required', 'manager_notification']:
        if field in data:
            setattr(interaction, field, bool(data[field]))
    
    # Update assigned_to
    if 'assigned_to' in data:
        if data['assigned_to']:
            assigned_user = User.query.get(data['assigned_to'])
            if not assigned_user:
                return jsonify({'error': 'Assigned user not found'}), 404
        interaction.assigned_to = data['assigned_to']
    
    # Update follow_up_date
    if 'follow_up_date' in data:
        if data['follow_up_date']:
            try:
                interaction.follow_up_date = datetime.fromisoformat(data['follow_up_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid follow_up_date format'}), 400
        else:
            interaction.follow_up_date = None
    
    # Update tags
    if 'tags' in data:
        if isinstance(data['tags'], list):
            interaction.tags = ','.join([tag.strip() for tag in data['tags'] if tag.strip()])
        else:
            interaction.tags = data['tags']
    
    db.session.commit()
    
    return jsonify(interaction.to_dict())

@interaction_bp.route('/interactions/<int:interaction_id>', methods=['DELETE'])
@login_required
def delete_interaction(interaction_id):
    # Only managers can delete interactions
    if current_user.role != 'manager':
        return jsonify({'error': 'Only managers can delete interactions'}), 403
    
    interaction = Interaction.query.get_or_404(interaction_id)
    db.session.delete(interaction)
    db.session.commit()
    
    return '', 204

# Comments endpoints
@interaction_bp.route('/interactions/<int:interaction_id>/comments', methods=['GET'])
@login_required
def get_interaction_comments(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Check permissions
    if current_user.role == 'agent' and interaction.agent_id != current_user.id and interaction.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    comments = InteractionComment.query.filter_by(interaction_id=interaction_id).order_by(InteractionComment.created_at.asc()).all()
    return jsonify([comment.to_dict() for comment in comments])

@interaction_bp.route('/interactions/<int:interaction_id>/comments', methods=['POST'])
@login_required
def add_interaction_comment(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Check permissions
    if current_user.role == 'agent' and interaction.agent_id != current_user.id and interaction.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    if not data.get('comment'):
        return jsonify({'error': 'Comment is required'}), 400
    
    comment = InteractionComment(
        interaction_id=interaction_id,
        user_id=current_user.id,
        comment=data['comment']
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify(comment.to_dict()), 201

# Quick actions
@interaction_bp.route('/interactions/<int:interaction_id>/resolve', methods=['POST'])
@login_required
def resolve_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Check permissions
    if current_user.role == 'agent' and interaction.agent_id != current_user.id and interaction.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json or {}
    
    interaction.status = 'resolved'
    interaction.resolved_at = datetime.utcnow()
    
    if data.get('resolution_notes'):
        interaction.resolution_notes = data['resolution_notes']
    
    db.session.commit()
    
    return jsonify(interaction.to_dict())

@interaction_bp.route('/interactions/<int:interaction_id>/escalate', methods=['POST'])
@login_required
def escalate_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Check permissions
    if current_user.role == 'agent' and interaction.agent_id != current_user.id and interaction.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json or {}
    
    interaction.status = 'escalated'
    interaction.manager_notification = True
    
    if data.get('assigned_to'):
        assigned_user = User.query.get(data['assigned_to'])
        if assigned_user and assigned_user.role == 'manager':
            interaction.assigned_to = data['assigned_to']
    
    # Add escalation comment
    if data.get('escalation_reason'):
        comment = InteractionComment(
            interaction_id=interaction_id,
            user_id=current_user.id,
            comment=f"Escalated to management. Reason: {data['escalation_reason']}"
        )
        db.session.add(comment)
    
    db.session.commit()
    
    return jsonify(interaction.to_dict())

@interaction_bp.route('/interactions/<int:interaction_id>/assign', methods=['POST'])
@login_required
def assign_interaction(interaction_id):
    # Only managers can assign interactions
    if current_user.role != 'manager':
        return jsonify({'error': 'Only managers can assign interactions'}), 403
    
    interaction = Interaction.query.get_or_404(interaction_id)
    data = request.json
    
    if not data.get('assigned_to'):
        return jsonify({'error': 'assigned_to is required'}), 400
    
    assigned_user = User.query.get(data['assigned_to'])
    if not assigned_user:
        return jsonify({'error': 'Assigned user not found'}), 404
    
    interaction.assigned_to = data['assigned_to']
    interaction.status = 'in_progress'
    
    # Add assignment comment
    comment = InteractionComment(
        interaction_id=interaction_id,
        user_id=current_user.id,
        comment=f"Assigned to {assigned_user.first_name} {assigned_user.last_name}"
    )
    db.session.add(comment)
    
    db.session.commit()
    
    return jsonify(interaction.to_dict())

# Analytics and reporting
@interaction_bp.route('/interactions/stats', methods=['GET'])
@login_required
def get_interaction_stats():
    # Base query
    query = Interaction.query
    
    # If user is an agent, only show their stats
    if current_user.role == 'agent':
        query = query.filter(Interaction.agent_id == current_user.id)
    
    # Get date range from query params
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(Interaction.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(Interaction.created_at <= date_to_obj)
        except ValueError:
            pass
    
    # Calculate statistics
    total_interactions = query.count()
    open_interactions = query.filter(Interaction.status == 'open').count()
    in_progress_interactions = query.filter(Interaction.status == 'in_progress').count()
    resolved_interactions = query.filter(Interaction.status == 'resolved').count()
    escalated_interactions = query.filter(Interaction.status == 'escalated').count()
    
    # Priority breakdown
    critical_interactions = query.filter(Interaction.priority_level == 'critical').count()
    high_interactions = query.filter(Interaction.priority_level == 'high').count()
    medium_interactions = query.filter(Interaction.priority_level == 'medium').count()
    low_interactions = query.filter(Interaction.priority_level == 'low').count()
    
    # Type breakdown
    type_stats = {}
    for interaction_type in Interaction.get_interaction_types():
        type_stats[interaction_type] = query.filter(Interaction.interaction_type == interaction_type).count()
    
    return jsonify({
        'total_interactions': total_interactions,
        'status_breakdown': {
            'open': open_interactions,
            'in_progress': in_progress_interactions,
            'resolved': resolved_interactions,
            'escalated': escalated_interactions
        },
        'priority_breakdown': {
            'critical': critical_interactions,
            'high': high_interactions,
            'medium': medium_interactions,
            'low': low_interactions
        },
        'type_breakdown': type_stats
    })

# Configuration endpoints
@interaction_bp.route('/interactions/config', methods=['GET'])
@login_required
def get_interaction_config():
    # Get all users for assignment dropdown
    users = User.query.all()
    
    return jsonify({
        'interaction_types': Interaction.get_interaction_types(),
        'priority_levels': Interaction.get_priority_levels(),
        'status_options': Interaction.get_status_options(),
        'users': [{'id': user.id, 'name': f"{user.first_name} {user.last_name}", 'role': user.role} for user in users]
    })

