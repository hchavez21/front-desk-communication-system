from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.user import db
from src.models.guest import Guest, GuestPreference
from src.models.reservation import Reservation
from src.models.interaction import Interaction
from datetime import datetime, date
from sqlalchemy import or_, and_

guest_bp = Blueprint('guest', __name__)

@guest_bp.route('/api/guests', methods=['GET'])
@login_required
def get_guests():
    """Get all guests with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Search parameters
        search = request.args.get('search', '').strip()
        guest_type = request.args.get('guest_type', '')
        vip_status = request.args.get('vip_status', '')
        loyalty_level = request.args.get('loyalty_level', '')
        
        # Build query
        query = Guest.query
        
        # Apply search filter
        if search:
            search_filter = or_(
                Guest.first_name.ilike(f'%{search}%'),
                Guest.last_name.ilike(f'%{search}%'),
                Guest.email.ilike(f'%{search}%'),
                Guest.phone.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Apply filters
        if guest_type:
            query = query.filter(Guest.guest_type == guest_type)
        
        if vip_status:
            query = query.filter(Guest.vip_status == (vip_status.lower() == 'true'))
        
        if loyalty_level:
            query = query.filter(Guest.loyalty_level == loyalty_level)
        
        # Order by last updated
        query = query.order_by(Guest.updated_at.desc())
        
        # Paginate
        guests = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'guests': [guest.to_dict() for guest in guests.items],
            'total': guests.total,
            'pages': guests.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': guests.has_next,
            'has_prev': guests.has_prev
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@guest_bp.route('/api/guests', methods=['POST'])
@login_required
def create_guest():
    """Create a new guest profile"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('first_name') or not data.get('last_name'):
            return jsonify({'error': 'First name and last name are required'}), 400
        
        # Check for duplicate email
        if data.get('email'):
            existing_guest = Guest.query.filter_by(email=data['email']).first()
            if existing_guest:
                return jsonify({'error': 'A guest with this email already exists'}), 400
        
        # Create new guest
        guest = Guest(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
            nationality=data.get('nationality'),
            id_document_type=data.get('id_document_type'),
            id_document_number=data.get('id_document_number'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            emergency_contact_relationship=data.get('emergency_contact_relationship'),
            special_needs=data.get('special_needs'),
            dietary_restrictions=data.get('dietary_restrictions'),
            accessibility_requirements=data.get('accessibility_requirements'),
            vip_status=data.get('vip_status', False),
            loyalty_level=data.get('loyalty_level'),
            guest_type=data.get('guest_type', 'individual'),
            corporate_account=data.get('corporate_account'),
            preferred_communication=data.get('preferred_communication', 'email'),
            marketing_consent=data.get('marketing_consent', False),
            # Legacy fields for backward compatibility
            room_number=data.get('room_number'),
            check_in_date=datetime.strptime(data['check_in_date'], '%Y-%m-%d').date() if data.get('check_in_date') else None,
            check_out_date=datetime.strptime(data['check_out_date'], '%Y-%m-%d').date() if data.get('check_out_date') else None,
            notes=data.get('notes'),
            created_by=current_user.id
        )
        
        db.session.add(guest)
        db.session.commit()
        
        return jsonify(guest.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@guest_bp.route('/api/guests/<int:guest_id>', methods=['GET'])
@login_required
def get_guest(guest_id):
    """Get a specific guest's details"""
    try:
        guest = Guest.query.get_or_404(guest_id)
        
        # Include additional details
        guest_data = guest.to_dict()
        
        # Add preferences
        preferences = GuestPreference.query.filter_by(guest_id=guest_id).all()
        guest_data['preferences'] = [pref.to_dict() for pref in preferences]
        
        # Add reservations if Reservation model exists
        try:
            reservations = Reservation.query.filter_by(guest_id=guest_id).order_by(Reservation.check_in_date.desc()).all()
            guest_data['reservations'] = [res.to_dict() for res in reservations]
        except:
            guest_data['reservations'] = []
        
        # Add recent interactions
        interactions = Interaction.query.filter_by(guest_id=guest_id).order_by(Interaction.created_at.desc()).limit(10).all()
        guest_data['recent_interactions'] = [interaction.to_dict() for interaction in interactions]
        
        return jsonify(guest_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Legacy routes for backward compatibility
@guest_bp.route('/guests', methods=['GET'])
@login_required
def get_guests_legacy():
    """Legacy route for backward compatibility"""
    # Get query parameters for search and filtering
    search = request.args.get('search', '')
    room_number = request.args.get('room_number', '')
    
    query = Guest.query
    
    if search:
        query = query.filter(
            (Guest.first_name.contains(search)) |
            (Guest.last_name.contains(search)) |
            (Guest.email.contains(search)) |
            (Guest.phone.contains(search))
        )
    
    if room_number:
        query = query.filter(Guest.room_number == room_number)
    
    guests = query.order_by(Guest.created_at.desc()).all()
    return jsonify([guest.to_dict() for guest in guests])

@guest_bp.route('/guests', methods=['POST'])
@login_required
def create_guest_legacy():
    """Legacy route for backward compatibility"""
    data = request.json
    
    # Validate required fields
    if not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'First name and last name are required'}), 400
    
    guest = Guest(
        first_name=data['first_name'],
        last_name=data['last_name'],
        room_number=data.get('room_number'),
        phone=data.get('phone'),
        email=data.get('email'),
        notes=data.get('notes')
    )
    
    # Handle dates
    if data.get('check_in_date'):
        try:
            guest.check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid check_in_date format. Use YYYY-MM-DD'}), 400
    
    if data.get('check_out_date'):
        try:
            guest.check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid check_out_date format. Use YYYY-MM-DD'}), 400
    
    db.session.add(guest)
    db.session.commit()
    
    return jsonify(guest.to_dict()), 201

@guest_bp.route('/guests/<int:guest_id>', methods=['GET'])
@login_required
def get_guest_legacy(guest_id):
    """Legacy route for backward compatibility"""
    guest = Guest.query.get_or_404(guest_id)
    return jsonify(guest.to_dict())

@guest_bp.route('/guests/<int:guest_id>', methods=['PUT'])
@login_required
def update_guest_legacy(guest_id):
    """Legacy route for backward compatibility"""
    guest = Guest.query.get_or_404(guest_id)
    data = request.json
    
    # Update fields
    guest.first_name = data.get('first_name', guest.first_name)
    guest.last_name = data.get('last_name', guest.last_name)
    guest.room_number = data.get('room_number', guest.room_number)
    guest.phone = data.get('phone', guest.phone)
    guest.email = data.get('email', guest.email)
    guest.notes = data.get('notes', guest.notes)
    
    # Handle dates
    if data.get('check_in_date'):
        try:
            guest.check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid check_in_date format. Use YYYY-MM-DD'}), 400
    
    if data.get('check_out_date'):
        try:
            guest.check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid check_out_date format. Use YYYY-MM-DD'}), 400
    
    guest.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(guest.to_dict())

@guest_bp.route('/guests/<int:guest_id>', methods=['DELETE'])
@login_required
def delete_guest_legacy(guest_id):
    """Legacy route for backward compatibility"""
    # Only managers can delete guests
    if current_user.role != 'manager':
        return jsonify({'error': 'Only managers can delete guests'}), 403
    
    guest = Guest.query.get_or_404(guest_id)
    db.session.delete(guest)
    db.session.commit()
    
    return '', 204

