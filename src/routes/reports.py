from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.models.user import db, User
from src.models.interaction import Interaction
from src.models.guest import Guest
from src.models.message import Message
from sqlalchemy import func, and_
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    # Get date range from query params (default to last 30 days)
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    stats = {}
    
    if current_user.role == 'manager':
        # Manager dashboard - all data
        stats['total_interactions'] = Interaction.query.filter(
            Interaction.created_at >= start_date
        ).count()
        
        stats['interactions_by_type'] = db.session.query(
            Interaction.interaction_type,
            func.count(Interaction.id).label('count')
        ).filter(
            Interaction.created_at >= start_date
        ).group_by(Interaction.interaction_type).all()
        
        stats['interactions_by_status'] = db.session.query(
            Interaction.status,
            func.count(Interaction.id).label('count')
        ).filter(
            Interaction.created_at >= start_date
        ).group_by(Interaction.status).all()
        
        stats['interactions_by_priority'] = db.session.query(
            Interaction.priority,
            func.count(Interaction.id).label('count')
        ).filter(
            Interaction.created_at >= start_date
        ).group_by(Interaction.priority).all()
        
        stats['top_agents'] = db.session.query(
            User.first_name,
            User.last_name,
            func.count(Interaction.id).label('interaction_count')
        ).join(Interaction).filter(
            Interaction.created_at >= start_date
        ).group_by(User.id).order_by(
            func.count(Interaction.id).desc()
        ).limit(5).all()
        
        stats['total_guests'] = Guest.query.count()
        stats['total_messages'] = Message.query.filter(
            Message.created_at >= start_date
        ).count()
        
    else:
        # Agent dashboard - only their data
        stats['my_interactions'] = Interaction.query.filter(
            and_(
                Interaction.agent_id == current_user.id,
                Interaction.created_at >= start_date
            )
        ).count()
        
        stats['my_interactions_by_type'] = db.session.query(
            Interaction.interaction_type,
            func.count(Interaction.id).label('count')
        ).filter(
            and_(
                Interaction.agent_id == current_user.id,
                Interaction.created_at >= start_date
            )
        ).group_by(Interaction.interaction_type).all()
        
        stats['my_interactions_by_status'] = db.session.query(
            Interaction.status,
            func.count(Interaction.id).label('count')
        ).filter(
            and_(
                Interaction.agent_id == current_user.id,
                Interaction.created_at >= start_date
            )
        ).group_by(Interaction.status).all()
    
    # Unread messages count for both roles
    stats['unread_messages'] = Message.query.filter(
        and_(
            ((Message.recipient_id == current_user.id) | (Message.is_announcement == True)),
            Message.is_read == False
        )
    ).count()
    
    # Convert query results to dictionaries
    for key, value in stats.items():
        if hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
            try:
                stats[key] = [{'type': item[0], 'count': item[1]} for item in value]
            except (IndexError, TypeError):
                pass
    
    return jsonify(stats)

@reports_bp.route('/reports/interactions', methods=['GET'])
@login_required
def get_interaction_report():
    # Only managers can access detailed reports
    if current_user.role != 'manager':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    interaction_type = request.args.get('type')
    agent_id = request.args.get('agent_id')
    
    query = Interaction.query
    
    # Apply date filters
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Interaction.created_at >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Add one day to include the entire end date
            end_date = end_date + timedelta(days=1)
            query = query.filter(Interaction.created_at < end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Apply other filters
    if interaction_type:
        query = query.filter(Interaction.interaction_type == interaction_type)
    
    if agent_id:
        query = query.filter(Interaction.agent_id == agent_id)
    
    interactions = query.order_by(Interaction.created_at.desc()).all()
    
    return jsonify({
        'interactions': [interaction.to_dict() for interaction in interactions],
        'total_count': len(interactions)
    })

@reports_bp.route('/reports/summary', methods=['GET'])
@login_required
def get_summary_report():
    # Only managers can access summary reports
    if current_user.role != 'manager':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get overall statistics
    total_users = User.query.count()
    total_agents = User.query.filter_by(role='agent').count()
    total_managers = User.query.filter_by(role='manager').count()
    total_guests = Guest.query.count()
    total_interactions = Interaction.query.count()
    total_messages = Message.query.count()
    
    # Get recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_interactions = Interaction.query.filter(
        Interaction.created_at >= week_ago
    ).count()
    recent_messages = Message.query.filter(
        Message.created_at >= week_ago
    ).count()
    
    # Get interaction statistics
    open_interactions = Interaction.query.filter_by(status='open').count()
    high_priority_interactions = Interaction.query.filter_by(priority='high').count()
    
    return jsonify({
        'users': {
            'total': total_users,
            'agents': total_agents,
            'managers': total_managers
        },
        'guests': {
            'total': total_guests
        },
        'interactions': {
            'total': total_interactions,
            'open': open_interactions,
            'high_priority': high_priority_interactions,
            'recent_week': recent_interactions
        },
        'messages': {
            'total': total_messages,
            'recent_week': recent_messages
        }
    })

