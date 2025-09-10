# Front Desk Communication System

A comprehensive web-based communication and guest management system designed for hotels and hospitality businesses. This system facilitates seamless communication between front desk agents and management while providing robust guest interaction tracking and management capabilities.

## 🌐 Live Demo

**Production URL:** https://xlhyimcdyv0v.manus.space

### Demo Credentials
- **Manager Access:** `admin` / `admin123`
- **Agent Access:** `agent1` / `agent123`

## ✨ Features

### 🏨 Guest Management
- **Comprehensive Guest Profiles:** Complete guest information including contact details, preferences, and special requirements
- **Reservation Management:** Track check-in/out dates, room assignments, and booking references
- **Guest History:** Maintain complete records of past stays and interactions
- **Advanced Search:** Find guests by name, room number, phone, email, or reservation details
- **Guest Preferences:** Track dietary restrictions, accessibility needs, and VIP status

### 📝 Interaction Logging
- **Detailed Interaction Forms:** Log comprehensive guest interactions with type, priority, and status tracking
- **Assignment System:** Assign interactions to specific team members
- **Follow-up Tracking:** Mark interactions requiring follow-up action
- **Management Alerts:** Notify management of critical interactions
- **Search & Analytics:** Find and analyze interaction patterns

### 💬 Internal Messaging
- **Real-time Communication:** Instant messaging between team members
- **Conversation Types:**
  - Direct Messages: Private one-on-one conversations
  - Group Chats: Team discussions with multiple participants
  - Announcements: Broadcast important information
  - Guest Discussions: Conversations about specific guests
- **Message Organization:** All messages organized by conversation threads
- **Participant Management:** Add/remove team members from conversations

### 👥 Role-Based Access Control
- **Manager Access:** Full system oversight with analytics and team management
- **Agent Access:** Personal dashboard and interaction logging capabilities
- **Secure Authentication:** Password-based login with session management

### 📊 Dashboard & Analytics
- **Real-time Statistics:** Track total interactions, open issues, and resolution rates
- **Recent Activity:** Quick view of latest guest interactions and team communications
- **Performance Metrics:** Monitor team performance and guest satisfaction trends

## 🛠️ Technology Stack

### Backend
- **Framework:** Flask (Python)
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** Flask-Login with password hashing
- **API:** RESTful endpoints with JSON responses
- **CORS:** Cross-origin resource sharing enabled

### Frontend
- **Framework:** React 18 with Vite
- **UI Components:** shadcn/ui component library
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Routing:** React Router DOM
- **State Management:** React Context API

### Deployment
- **Backend:** Flask production server
- **Frontend:** Static build served by Flask
- **Hosting:** Manus deployment platform
- **Database:** SQLite with automatic initialization

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or pnpm

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hchavez21/front-desk-communication-system.git
   cd front-desk-communication-system
   ```

2. **Set up Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask backend:**
   ```bash
   cd src
   python main.py
   ```

The backend will be available at `http://localhost:5001`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd front-desk-ui
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   # or
   pnpm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   pnpm run dev
   ```

The frontend will be available at `http://localhost:5173`

### Production Build

1. **Build the frontend:**
   ```bash
   cd front-desk-ui
   npm run build
   ```

2. **Copy build to Flask static directory:**
   ```bash
   cp -r dist/* ../src/static/
   ```

3. **Run Flask in production mode:**
   ```bash
   cd ../src
   python main.py
   ```

## 📁 Project Structure

```
front-desk-communication-system/
├── src/                          # Flask backend
│   ├── models/                   # Database models
│   │   ├── user.py              # User authentication model
│   │   ├── guest.py             # Guest management model
│   │   ├── interaction.py       # Interaction logging model
│   │   ├── conversation.py      # Messaging system models
│   │   └── reservation.py       # Reservation management model
│   ├── routes/                   # API endpoints
│   │   ├── auth.py              # Authentication routes
│   │   ├── guest.py             # Guest management API
│   │   ├── interaction.py       # Interaction logging API
│   │   ├── messaging.py         # Internal messaging API
│   │   └── reports.py           # Analytics and reports API
│   ├── static/                   # Frontend build files
│   ├── database/                 # SQLite database
│   └── main.py                   # Flask application entry point
├── front-desk-ui/                # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── Dashboard.jsx     # Main dashboard
│   │   │   ├── GuestList.jsx     # Guest management
│   │   │   ├── InteractionForm.jsx # Interaction logging
│   │   │   ├── MessagingSystem.jsx # Internal messaging
│   │   │   └── Layout.jsx        # Main layout
│   │   ├── contexts/             # React contexts
│   │   │   └── AuthContext.jsx   # Authentication context
│   │   └── App.jsx               # Main application component
│   ├── public/                   # Static assets
│   └── package.json              # Node.js dependencies
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session management
- `DATABASE_URL`: Database connection string (defaults to SQLite)

### Default Users
The system automatically creates default users on first run:
- **Manager:** username `admin`, password `admin123`
- **Agent:** username `agent1`, password `agent123`

## 📖 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Guest Management Endpoints
- `GET /api/guests` - List all guests with search/filter
- `POST /api/guests` - Create new guest
- `GET /api/guests/{id}` - Get guest details
- `PUT /api/guests/{id}` - Update guest information
- `DELETE /api/guests/{id}` - Delete guest

### Interaction Logging Endpoints
- `GET /api/interactions` - List interactions with filters
- `POST /api/interactions` - Log new interaction
- `GET /api/interactions/{id}` - Get interaction details
- `PUT /api/interactions/{id}` - Update interaction
- `DELETE /api/interactions/{id}` - Delete interaction

### Messaging Endpoints
- `GET /api/conversations` - List user conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}/messages` - Get conversation messages
- `POST /api/conversations/{id}/messages` - Send message

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please open an issue on GitHub or contact the development team.

## 🙏 Acknowledgments

- Built with Flask and React
- UI components from shadcn/ui
- Icons from Lucide React
- Styling with Tailwind CSS

---

**Made with ❤️ for the hospitality industry**

