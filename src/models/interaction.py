from src.models.user import db
from datetime import datetime

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Basic interaction information
    interaction_type = db.Column(db.String(50), nullable=False)  # check-in, complaint, request, inquiry, maintenance, billing, compliment, emergency, other
    priority_level = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), nullable=False, default='open')  # open, in_progress, resolved, escalated, closed
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=True)  # lobby, room, restaurant, etc.
    
    # Guest information (for cases where guest is not in system)
    guest_name = db.Column(db.String(100), nullable=True)
    room_number = db.Column(db.String(20), nullable=True)
    guest_phone = db.Column(db.String(20), nullable=True)
    guest_email = db.Column(db.String(100), nullable=True)
    reservation_number = db.Column(db.String(50), nullable=True)
    
    # Follow-up information
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager_notification = db.Column(db.Boolean, default=False)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Additional fields
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    guest_info = db.relationship('Guest', lazy=True)
    agent = db.relationship('User', foreign_keys=[agent_id], lazy=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], lazy=True)
    comments = db.relationship('InteractionComment', backref='interaction', lazy=True, cascade='all, delete-orphan')
    attachments = db.relationship('InteractionAttachment', backref='interaction', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Interaction {self.subject}>'

    def to_dict(self, include_comments=False, include_attachments=False):
        result = {
            'id': self.id,
            'guest_id': self.guest_id,
            'agent_id': self.agent_id,
            'interaction_type': self.interaction_type,
            'priority_level': self.priority_level,
            'status': self.status,
            'subject': self.subject,
            'description': self.description,
            'location': self.location,
            'guest_name': self.guest_name,
            'room_number': self.room_number,
            'guest_phone': self.guest_phone,
            'guest_email': self.guest_email,
            'reservation_number': self.reservation_number,
            'follow_up_required': self.follow_up_required,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'assigned_to': self.assigned_to,
            'manager_notification': self.manager_notification,
            'resolution_notes': self.resolution_notes,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'guest': self.guest_info.to_dict() if self.guest_info else None,
            'agent': {
                'id': self.agent.id,
                'first_name': self.agent.first_name,
                'last_name': self.agent.last_name,
                'username': self.agent.username,
                'role': self.agent.role
            } if self.agent else None,
            'assigned_user': {
                'id': self.assigned_user.id,
                'first_name': self.assigned_user.first_name,
                'last_name': self.assigned_user.last_name,
                'username': self.assigned_user.username,
                'role': self.assigned_user.role
            } if self.assigned_user else None
        }
        
        if include_comments:
            result['comments'] = [comment.to_dict() for comment in self.comments]
        
        if include_attachments:
            result['attachments'] = [attachment.to_dict() for attachment in self.attachments]
            
        return result

    @staticmethod
    def get_interaction_types():
        return [
            'check-in', 'check-out', 'complaint', 'request', 'inquiry', 
            'maintenance', 'billing', 'compliment', 'emergency', 'other'
        ]
    
    @staticmethod
    def get_priority_levels():
        return ['low', 'medium', 'high', 'critical']
    
    @staticmethod
    def get_status_options():
        return ['open', 'in_progress', 'resolved', 'escalated', 'closed']


class InteractionComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interaction_id = db.Column(db.Integer, db.ForeignKey('interaction.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='interaction_comments', lazy=True)
    
    def __repr__(self):
        return f'<InteractionComment {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'interaction_id': self.interaction_id,
            'user_id': self.user_id,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': {
                'id': self.user.id,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'username': self.user.username,
                'role': self.user.role
            } if self.user else None
        }


class InteractionAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interaction_id = db.Column(db.Integer, db.ForeignKey('interaction.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_attachments', lazy=True)
    
    def __repr__(self):
        return f'<InteractionAttachment {self.filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'interaction_id': self.interaction_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'uploader': {
                'id': self.uploader.id,
                'first_name': self.uploader.first_name,
                'last_name': self.uploader.last_name,
                'username': self.uploader.username
            } if self.uploader else None
        }

