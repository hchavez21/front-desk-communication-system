from src.models.user import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'legacy_message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # NULL for announcements
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_announcement = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.subject}>'

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'content': self.content,
            'is_announcement': self.is_announcement,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sender': {
                'id': self.sender.id,
                'first_name': self.sender.first_name,
                'last_name': self.sender.last_name,
                'username': self.sender.username,
                'role': self.sender.role
            } if self.sender else None,
            'recipient': {
                'id': self.recipient.id,
                'first_name': self.recipient.first_name,
                'last_name': self.recipient.last_name,
                'username': self.recipient.username,
                'role': self.recipient.role
            } if self.recipient else None
        }

