import React, { JSX } from 'react';
import { authService } from './services/authService';
import './styles/globals.css';
import {
    BrowserRouter as Router,
    Routes,
    Route,
    Navigate,
} from 'react-router-dom';
import { Admin } from './pages/AdminPage';  
import { Dashboard } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';

// check authorize
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    const isAuthenticated = document.cookie.includes('access_token');
    const isUser = document.cookie.includes('user_role=MANAGER');
    
    if (!isAuthenticated) return <Navigate to="/login" replace />;
    if (!isUser) return <Navigate to="/login" replace />;

    return children;
};

// check role
const AdminProtectedRoute = ({ children }: { children: JSX.Element }) => {
    const isAuthenticated = document.cookie.includes('access_token');
    const isAdmin = document.cookie.includes('user_role=ADMIN');
    
    if (!isAuthenticated) return <Navigate to="/login" replace />;
    if (!isAdmin) return <Navigate to="/login" replace />;
    
    return children;
};

export default function App() {
    return (
        <Router>
            <Routes>
                {/* Route for Login */}
                <Route path="/login" element={<LoginPage />} />

                {/* Route for User -> MainPage (Dashboard) */}
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />

                {/* Route for Admin */}
                <Route path="/admin" element={
                    <AdminProtectedRoute>
                        <Admin />
                    </AdminProtectedRoute>} />

                {/* Chuyển hướng các đường dẫn lạ về trang chính */}
                <Route path="*" 
                    // element={<Navigate to="/" />} 
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </Router>
    );
}
