import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import InteractionList from './components/InteractionList';
import InteractionForm from './components/InteractionForm';
import InteractionDetail from './components/InteractionDetail';
import GuestList from './components/GuestList';
import MessagingSystem from './components/MessagingSystem';
import './App.css';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Interaction Detail Wrapper
const InteractionDetailWrapper = () => {
  const { id } = useParams();
  return <InteractionDetail interactionId={id} />;
};

// Interaction Edit Wrapper
const InteractionEditWrapper = () => {
  const { id } = useParams();
  return <InteractionForm interactionId={id} />;
};

// Main App Routes
const AppRoutes = () => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} 
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/guests"
        element={
          <ProtectedRoute>
            <Layout>
              <GuestList />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/messages"
        element={
          <ProtectedRoute>
            <MessagingSystem />
          </ProtectedRoute>
        }
      />
      <Route
        path="/interactions"
        element={
          <ProtectedRoute>
            <Layout>
              <InteractionList />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interactions/new"
        element={
          <ProtectedRoute>
            <Layout>
              <InteractionForm />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interactions/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <InteractionDetailWrapper />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interactions/:id/edit"
        element={
          <ProtectedRoute>
            <Layout>
              <InteractionEditWrapper />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/messages"
        element={
          <ProtectedRoute>
            <Layout>
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Messages</h2>
                <p className="text-gray-600">Messaging system coming soon...</p>
              </div>
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <Layout>
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Reports</h2>
                <p className="text-gray-600">Reports and analytics coming soon...</p>
              </div>
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
