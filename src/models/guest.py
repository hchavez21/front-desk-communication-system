from src.models.user import db
from datetime import datetime

class Guest(db.Model):
    __tablename__ = 'guest'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Additional Details
    date_of_birth = db.Column(db.Date, nullable=True)
    nationality = db.Column(db.String(100), nullable=True)
    id_document_type = db.Column(db.String(50), nullable=True)  # passport, driver_license, national_id
    id_document_number = db.Column(db.String(100), nullable=True)
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(200), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_relationship = db.Column(db.String(100), nullable=True)
    
    # Special Requirements
    special_needs = db.Column(db.Text, nullable=True)
    dietary_restrictions = db.Column(db.Text, nullable=True)
    accessibility_requirements = db.Column(db.Text, nullable=True)
    
    # Guest Classification
    vip_status = db.Column(db.Boolean, default=False)
    loyalty_level = db.Column(db.String(50), nullable=True)  # bronze, silver, gold, platinum
    guest_type = db.Column(db.String(50), default='individual')  # individual, corporate, group
    corporate_account = db.Column(db.String(200), nullable=True)
    
    # Communication Preferences
    preferred_communication = db.Column(db.String(50), default='email')  # email, sms, phone
    marketing_consent = db.Column(db.Boolean, default=False)
    
    # Legacy fields for backward compatibility
    room_number = db.Column(db.String(10))
    check_in_date = db.Column(db.Date)
    check_out_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    reservations = db.relationship('Reservation', foreign_keys='Reservation.guest_id', backref='guest_profile', lazy=True, cascade='all, delete-orphan')
    preferences = db.relationship('GuestPreference', backref='guest_profile', lazy=True, cascade='all, delete-orphan')
    interactions = db.relationship('Interaction', backref='guest', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_reservation(self):
        """Get the current active reservation for this guest"""
        today = datetime.utcnow().date()
        return next((r for r in self.reservations 
                    if r.check_in_date <= today <= r.check_out_date 
                    and r.status in ['confirmed', 'checked_in']), None)
    
    @property
    def total_stays(self):
        """Get the total number of completed stays"""
        return len([r for r in self.reservations if r.status == 'checked_out'])
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'nationality': self.nationality,
            'id_document_type': self.id_document_type,
            'id_document_number': self.id_document_number,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relationship': self.emergency_contact_relationship,
            'special_needs': self.special_needs,
            'dietary_restrictions': self.dietary_restrictions,
            'accessibility_requirements': self.accessibility_requirements,
            'vip_status': self.vip_status,
            'loyalty_level': self.loyalty_level,
            'guest_type': self.guest_type,
            'corporate_account': self.corporate_account,
            'preferred_communication': self.preferred_communication,
            'marketing_consent': self.marketing_consent,
            'total_stays': self.total_stays,
            'current_reservation': self.current_reservation.to_dict() if self.current_reservation else None,
            # Legacy fields
            'room_number': self.room_number,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None,
            'check_out_date': self.check_out_date.isoformat() if self.check_out_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GuestPreference(db.Model):
    __tablename__ = 'guest_preference'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    
    # Preference Details
    preference_category = db.Column(db.String(50), nullable=False)  # room, service, dietary, communication
    preference_type = db.Column(db.String(100), nullable=False)  # floor_level, bed_type, housekeeping_time, etc.
    preference_value = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def __repr__(self):
        return f'<GuestPreference {self.preference_type}: {self.preference_value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'guest_id': self.guest_id,
            'preference_category': self.preference_category,
            'preference_type': self.preference_type,
            'preference_value': self.preference_value,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

