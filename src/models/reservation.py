from src.models.user import db
from datetime import datetime

class Reservation(db.Model):
    __tablename__ = 'reservation'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Guest Information
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    
    # Reservation Details
    reservation_number = db.Column(db.String(50), unique=True, nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    actual_check_in = db.Column(db.DateTime, nullable=True)
    actual_check_out = db.Column(db.DateTime, nullable=True)
    
    # Room Information
    room_number = db.Column(db.String(20), nullable=True)
    room_type = db.Column(db.String(100), nullable=True)  # standard, deluxe, suite, etc.
    floor_preference = db.Column(db.String(50), nullable=True)  # low, high, specific
    view_preference = db.Column(db.String(100), nullable=True)  # ocean, city, garden, etc.
    
    # Booking Information
    booking_source = db.Column(db.String(100), nullable=True)  # direct, booking.com, expedia, etc.
    rate_plan = db.Column(db.String(100), nullable=True)
    base_rate = db.Column(db.Numeric(10, 2), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(3), default='USD')
    
    # Guest Count
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    infants = db.Column(db.Integer, default=0)
    
    # Status and Special Requests
    status = db.Column(db.String(50), default='confirmed')  # confirmed, checked_in, checked_out, cancelled, no_show
    special_requests = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    
    # Payment Information
    payment_status = db.Column(db.String(50), default='pending')  # pending, partial, paid, refunded
    deposit_amount = db.Column(db.Numeric(10, 2), nullable=True)
    balance_due = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Group Booking
    group_name = db.Column(db.String(200), nullable=True)
    group_leader_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=True)
    is_group_booking = db.Column(db.Boolean, default=False)
    
    # System Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    guest = db.relationship('Guest', foreign_keys=[guest_id], backref='guest_reservations')
    group_leader = db.relationship('Guest', foreign_keys=[group_leader_id])
    
    def __repr__(self):
        return f'<Reservation {self.reservation_number}>'
    
    @property
    def duration_nights(self):
        """Calculate the number of nights for this reservation"""
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return 0
    
    @property
    def is_current(self):
        """Check if this is a current reservation"""
        today = datetime.utcnow().date()
        return (self.check_in_date <= today <= self.check_out_date and 
                self.status in ['confirmed', 'checked_in'])
    
    @property
    def is_past(self):
        """Check if this is a past reservation"""
        today = datetime.utcnow().date()
        return self.check_out_date < today or self.status in ['checked_out', 'cancelled']
    
    @property
    def is_future(self):
        """Check if this is a future reservation"""
        today = datetime.utcnow().date()
        return self.check_in_date > today and self.status == 'confirmed'
    
    def to_dict(self):
        return {
            'id': self.id,
            'guest_id': self.guest_id,
            'reservation_number': self.reservation_number,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None,
            'check_out_date': self.check_out_date.isoformat() if self.check_out_date else None,
            'actual_check_in': self.actual_check_in.isoformat() if self.actual_check_in else None,
            'actual_check_out': self.actual_check_out.isoformat() if self.actual_check_out else None,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'floor_preference': self.floor_preference,
            'view_preference': self.view_preference,
            'booking_source': self.booking_source,
            'rate_plan': self.rate_plan,
            'base_rate': float(self.base_rate) if self.base_rate else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'currency': self.currency,
            'adults': self.adults,
            'children': self.children,
            'infants': self.infants,
            'status': self.status,
            'special_requests': self.special_requests,
            'internal_notes': self.internal_notes,
            'payment_status': self.payment_status,
            'deposit_amount': float(self.deposit_amount) if self.deposit_amount else None,
            'balance_due': float(self.balance_due) if self.balance_due else None,
            'group_name': self.group_name,
            'group_leader_id': self.group_leader_id,
            'is_group_booking': self.is_group_booking,
            'duration_nights': self.duration_nights,
            'is_current': self.is_current,
            'is_past': self.is_past,
            'is_future': self.is_future,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

