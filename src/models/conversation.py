from src.models.user import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Conversation Details
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    conversation_type = db.Column(db.String(50), default='direct')  # direct, group, broadcast, guest_related
    
    # Guest Context (if applicable)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=True)
    
    # Conversation Settings
    is_archived = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)  # Prevent new messages
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    guest = db.relationship('Guest', backref='conversations')
    participants = db.relationship('ConversationParticipant', backref='conversation', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('ConversationMessage', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.title or self.id}>'
    
    @property
    def last_message(self):
        """Get the most recent message in this conversation"""
        return ConversationMessage.query.filter_by(conversation_id=self.id).order_by(ConversationMessage.created_at.desc()).first()
    
    @property
    def message_count(self):
        """Get the total number of messages in this conversation"""
        return ConversationMessage.query.filter_by(conversation_id=self.id).count()
    
    @property
    def participant_count(self):
        """Get the number of participants in this conversation"""
        return ConversationParticipant.query.filter_by(conversation_id=self.id).count()
    
    def get_participants(self):
        """Get all participants in this conversation"""
        return [p.user for p in self.participants]
    
    def has_participant(self, user_id):
        """Check if a user is a participant in this conversation"""
        return ConversationParticipant.query.filter_by(
            conversation_id=self.id, 
            user_id=user_id
        ).first() is not None
    
    def get_unread_count(self, user_id):
        """Get the number of unread messages for a specific user"""
        participant = ConversationParticipant.query.filter_by(
            conversation_id=self.id, 
            user_id=user_id
        ).first()
        
        if not participant:
            return 0
        
        if not participant.last_read_at:
            return self.message_count
        
        return ConversationMessage.query.filter(
            ConversationMessage.conversation_id == self.id,
            ConversationMessage.created_at > participant.last_read_at
        ).count()
    
    def to_dict(self, user_id=None):
        last_msg = self.last_message
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'conversation_type': self.conversation_type,
            'guest_id': self.guest_id,
            'guest': self.guest.to_dict() if self.guest else None,
            'is_archived': self.is_archived,
            'is_pinned': self.is_pinned,
            'is_locked': self.is_locked,
            'message_count': self.message_count,
            'participant_count': self.participant_count,
            'participants': [p.user.to_dict() for p in self.participants],
            'last_message': last_msg.to_dict() if last_msg else None,
            'unread_count': self.get_unread_count(user_id) if user_id else 0,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ConversationParticipant(db.Model):
    __tablename__ = 'conversation_participant'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Participant Settings
    role = db.Column(db.String(50), default='member')  # member, admin, moderator
    is_muted = db.Column(db.Boolean, default=False)
    last_read_at = db.Column(db.DateTime, nullable=True)
    
    # System Fields
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='conversation_participations')
    
    def __repr__(self):
        return f'<ConversationParticipant {self.user_id} in {self.conversation_id}>'
    
    def mark_as_read(self):
        """Mark all messages in this conversation as read for this participant"""
        self.last_read_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'user': self.user.to_dict(),
            'role': self.role,
            'is_muted': self.is_muted,
            'last_read_at': self.last_read_at.isoformat() if self.last_read_at else None,
            'joined_at': self.joined_at.isoformat()
        }

class ConversationMessage(db.Model):
    __tablename__ = 'conversation_message'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Message Content
    message_type = db.Column(db.String(50), default='text')  # text, file, image, system
    content = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    
    # Message Properties
    is_priority = db.Column(db.Boolean, default=False)
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    reply_to_message_id = db.Column(db.Integer, db.ForeignKey('conversation_message.id'), nullable=True)
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', backref='conversation_messages')
    reply_to = db.relationship('ConversationMessage', remote_side=[id], backref='replies')
    reactions = db.relationship('MessageReaction', backref='message', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ConversationMessage {self.id} from {self.sender_id}>'
    
    def get_reactions_summary(self):
        """Get a summary of reactions to this message"""
        reactions = {}
        for reaction in self.reactions:
            if reaction.reaction_type not in reactions:
                reactions[reaction.reaction_type] = []
            reactions[reaction.reaction_type].append(reaction.user.to_dict())
        return reactions
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender': self.sender.to_dict(),
            'message_type': self.message_type,
            'content': self.content,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'is_priority': self.is_priority,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_to': self.reply_to.to_dict() if self.reply_to else None,
            'reactions': self.get_reactions_summary(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MessageReaction(db.Model):
    __tablename__ = 'message_reaction'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('conversation_message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Reaction Details
    reaction_type = db.Column(db.String(50), nullable=False)  # like, love, laugh, angry, sad, acknowledge
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='message_reactions')
    
    # Unique constraint to prevent duplicate reactions
    __table_args__ = (db.UniqueConstraint('message_id', 'user_id', 'reaction_type'),)
    
    def __repr__(self):
        return f'<MessageReaction {self.reaction_type} by {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'user': self.user.to_dict(),
            'reaction_type': self.reaction_type,
            'created_at': self.created_at.isoformat()
        }

