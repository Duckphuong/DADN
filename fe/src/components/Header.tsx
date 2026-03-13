import { useNavigate } from 'react-router-dom';
import { Droplets, LogOut } from 'lucide-react';

export function Header() {
    const navigate = useNavigate();

    const handleLogout = () => {
        navigate('/login');
    };

    return (
        <header className="bg-gradient-to-r from-cyan-600 via-blue-600 to-blue-700 text-white shadow-lg">
            <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        {/* Droplet Icon */}
                        <div className="flex flex-col gap-2">
                            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                                <Droplets className="w-12 h-12 text-cyan-200" />
                            </div>
                        </div>
                        {/* Tiêu đề */}
                        <div className="flex-1">
                            <h1 className="text-2xl text-white">
                                AI-Based Water Quality Prediction &
                                Contamination Alert System
                            </h1>
                            <p className="text-cyan-100 text-lg">
                                Real-Time IoT + AI Monitoring
                            </p>
                        </div>
                    </div>
                    {/* Logout Button */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={handleLogout}
                            className="group flex items-center justify-center bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-red-500/40 transition-all duration-300"
                            style={{
                                width: '65.4px',
                                height: '65.4px',
                                borderRadius: '16px',
                            }}
                            title="Logout"
                        >
                            <LogOut className="w-8 h-8 text-white group-hover:scale-110 transition-transform" />
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}
