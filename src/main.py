import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
from src.models.user import db, User
from src.models.guest import Guest, GuestPreference
from src.models.reservation import Reservation
from src.models.interaction import Interaction
from src.models.conversation import Conversation, ConversationParticipant, ConversationMessage, MessageReaction
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.guest import guest_bp
from src.routes.interaction import interaction_bp
from src.routes.messaging import messaging_bp
from src.routes.reports import reports_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(guest_bp, url_prefix='/api')
app.register_blueprint(interaction_bp, url_prefix='/api')
app.register_blueprint(messaging_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
    
    # Create default admin user if none exists
    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@frontdesk.com',
            first_name='System',
            last_name='Administrator',
            role='manager'
        )
        admin.set_password('admin123')
        
        agent = User(
            username='agent1',
            email='agent1@frontdesk.com',
            first_name='Front Desk',
            last_name='Agent',
            role='agent'
        )
        agent.set_password('agent123')
        
        db.session.add(admin)
        db.session.add(agent)
        db.session.commit()
        print("Default users created:")
        print("Manager - Username: admin, Password: admin123")
        print("Agent - Username: agent1, Password: agent123")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
