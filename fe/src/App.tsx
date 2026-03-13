import React, { JSX } from 'react';
import './styles/globals.css';
import {
    BrowserRouter as Router,
    Routes,
    Route,
    Navigate,
} from 'react-router-dom';
import { Header } from './components/Header';
import { SensorCard } from './components/SensorCard';
import { WaterClassificationPanel } from './components/WaterClassificationPanel';
import { AIPredictionPanel } from './components/AIPredictionPanel';
import { TrendCharts } from './components/TrendCharts';
import { MapVisualization } from './components/MapVisualization';
import { AlertsPanel } from './components/AlertsPanel';
import { SystemArchitecture } from './components/SystemArchitecture';
import { Footer } from './components/Footer';
import { LoginPage } from './components/LoginPage'; // Đảm bảo tên export là đúng
import { Droplet, Thermometer, Zap, Eye, Wind, Waves } from 'lucide-react';
import Predict from './components/Predict';
import PredictTable from './components/PredictTable';

// check authorize
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    const isAuthenticated = document.cookie.includes('user_session'); // Check for cookie
    return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// Main Page (Dashboard)
const Dashboard = () => {
    const sensorData = {
        pH: {
            value: 7.2,
            status: 'Neutral',
            statusColor: 'text-green-600',
            bgColor: 'bg-green-50',
        },
        temperature: {
            value: 24.5,
            status: 'Safe',
            statusColor: 'text-green-600',
            bgColor: 'bg-green-50',
        },
        conductivity: {
            value: 450,
            status: 'Medium salinity',
            statusColor: 'text-yellow-600',
            bgColor: 'bg-yellow-50',
        },
        turbidity: {
            value: 3.2,
            status: 'Slightly Cloudy',
            statusColor: 'text-yellow-600',
            bgColor: 'bg-yellow-50',
        },
        dissolvedOxygen: {
            value: 7.8,
            status: 'Good',
            statusColor: 'text-green-600',
            bgColor: 'bg-green-50',
        },
        hardness: {
            value: 180,
            status: 'Hard Water',
            statusColor: 'text-blue-600',
            bgColor: 'bg-blue-50',
        },
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-blue-100">
            <Header />
            <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
                <section>
                    <h2 className="text-cyan-900 mb-6">
                        Real-Time Sensor Readings
                    </h2>
                    <PredictTable />
                    <Predict />
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <SensorCard
                            icon={<Droplet className="w-8 h-8" />}
                            title="pH Value"
                            value={sensorData.pH.value.toFixed(1)}
                            unit=""
                            range="0–14"
                            status={sensorData.pH.status}
                            statusColor={sensorData.pH.statusColor}
                            bgColor={sensorData.pH.bgColor}
                            iconColor="text-blue-500"
                        />
                        <SensorCard
                            icon={<Thermometer className="w-8 h-8" />}
                            title="Temperature"
                            value={sensorData.temperature.value.toFixed(1)}
                            unit="°C"
                            range="0–50"
                            status={sensorData.temperature.status}
                            statusColor={sensorData.temperature.statusColor}
                            bgColor={sensorData.temperature.bgColor}
                            iconColor="text-orange-500"
                        />
                        <SensorCard
                            icon={<Zap className="w-8 h-8" />}
                            title="Conductivity"
                            value={sensorData.conductivity.value}
                            unit="µS/cm"
                            range="0–2000"
                            status={sensorData.conductivity.status}
                            statusColor={sensorData.conductivity.statusColor}
                            bgColor={sensorData.conductivity.bgColor}
                            iconColor="text-yellow-500"
                        />
                        <SensorCard
                            icon={<Eye className="w-8 h-8" />}
                            title="Turbidity"
                            value={sensorData.turbidity.value.toFixed(1)}
                            unit="NTU"
                            range="0–10"
                            status={sensorData.turbidity.status}
                            statusColor={sensorData.turbidity.statusColor}
                            bgColor={sensorData.turbidity.bgColor}
                            iconColor="text-gray-500"
                        />
                        <SensorCard
                            icon={<Wind className="w-8 h-8" />}
                            title="Dissolved Oxygen"
                            value={sensorData.dissolvedOxygen.value.toFixed(1)}
                            unit="mg/L"
                            range="0–15"
                            status={sensorData.dissolvedOxygen.status}
                            statusColor={sensorData.dissolvedOxygen.statusColor}
                            bgColor={sensorData.dissolvedOxygen.bgColor}
                            iconColor="text-cyan-500"
                        />
                        <SensorCard
                            icon={<Waves className="w-8 h-8" />}
                            title="Water Hardness"
                            value={sensorData.hardness.value}
                            unit="mg L⁻¹"
                            range="0–1000"
                            status={`${sensorData.hardness.status} (Soft < 60)`}
                            statusColor={sensorData.hardness.statusColor}
                            bgColor={sensorData.hardness.bgColor}
                            iconColor="text-indigo-500"
                        />
                    </div>
                </section>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <WaterClassificationPanel />
                    <AIPredictionPanel />
                </div>
                <TrendCharts />
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        <MapVisualization />
                    </div>
                    <div>
                        <AlertsPanel />
                    </div>
                </div>
                <SystemArchitecture />
            </main>
            <Footer />
        </div>
    );
};

export default function App() {
    return (
        <Router>
            <Routes>
                {/* Route for Login */}
                <Route path="/login" element={<LoginPage />} />

                {/* Route for MainPage (Dashboard) */}
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />

                {/* Chuyển hướng các đường dẫn lạ về trang chính */}
                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </Router>
    );
}
