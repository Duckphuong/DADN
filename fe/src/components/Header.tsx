import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Droplets, LogOut, Settings, Key, XCircle, Loader2, Save, Eye, EyeOff, ShieldAlert } from 'lucide-react';
import { authService } from '../services/authService';

export function Header() {
	// const navigate = useNavigate();
	const userRole = authService.getUserRole();

	const [showCurrentPass, setShowCurrentPass] = useState(false);
	const [showNewPass, setShowNewPass] = useState(false);
	// State quản lý dropdown và modal
	const [isMenuOpen, setIsMenuOpen] = useState(false);
	const [isChangePassOpen, setIsChangePassOpen] = useState(false);
	
	// State cho form đổi mật khẩu
	const [passwords, setPasswords] = useState({ current: '', new: '' });
	const [curPassError, setCurPassError] = useState('');
	const [isSaving, setIsSaving] = useState(false);

	const handleLogout = async () => {
		try {
			await authService.logout();
		} catch (error) {
			console.error("Logout failed in component:", error);
		}
	};

	const handleChangePassword = async (e: React.FormEvent) => {
		e.preventDefault();
		setIsSaving(true);
		try {
			await authService.changePassword({
				currentPassword: passwords.current, 
				newPassword: passwords.new
			});

			alert("Password changed successfully!");
			setPasswords({ current: '', new: '' });
			setIsChangePassOpen(false);
		} catch (error: any) {
			// const errorMsg = error.response?.data?.message || error.response?.data?.error || "Invalid request data";
			setCurPassError('Incorrect Current Password')
			// alert(`Error: ${errorMsg}`);
		} finally {
			setIsSaving(false);
		}
	};

	return (
		<header className="bg-gradient-to-r from-cyan-600 via-blue-600 to-blue-700 text-white shadow-lg relative">
			<div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-6">
						{/* Droplet Icon */}
						<div className="flex flex-col gap-2">
							<div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
								{userRole === 'ADMIN' ? (
									<ShieldAlert className="w-12 h-12 text-cyan-200" />
								) : (
									<Droplets className="w-12 h-12 text-cyan-200" />
								)}
							</div>
						</div>
						{/* Tiêu đề */}
						<div className="flex-1">
							<h1 className="text-2xl text-white font-semibold">
								{userRole === 'ADMIN' ? 'User Management' : 'AI-Based Water Quality Prediction \& Contamination Alert System'}
							</h1>
							<p className="text-cyan-100 text-lg">
								{userRole === 'ADMIN' ? 'Manage system access, roles, and permissions' : 'Real-Time IoT + AI Monitoring'}
							</p>
						</div>
					</div>

					{/* Settings Button & Dropdown */}
					<div className="relative">
						<button
							onClick={() => setIsMenuOpen(!isMenuOpen)}
							className="group flex flex-col items-center gap-1 bg-white/10 backdrop-blur-sm p-3 rounded-xl border border-white/20 hover:bg-white/20 transition-all"
						>
							<Settings className={`w-6 h-6 text-white transition-transform duration-300 ${isMenuOpen ? 'rotate-90' : ''}`} />
							<span className="text-[10px] uppercase tracking-wider">Settings</span>
						</button>

						{/* Dropdown Menu */}
						{isMenuOpen && (
							<>
								<div className="fixed inset-0 z-10" onClick={() => setIsMenuOpen(false)}></div>
								<div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-xl border border-gray-100 py-2 z-20 animate-in fade-in slide-in-from-top-2">
									<button
										onClick={() => { setIsChangePassOpen(true); setIsMenuOpen(false); }}
										className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
									>
										<Key size={16} className="text-cyan-600" />
										Change Password
									</button>
									<div className="h-px bg-gray-100 my-1"></div>
									<button
										onClick={handleLogout}
										className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
									>
										<LogOut size={16} />
										Logout
									</button>
								</div>
							</>
						)}
					</div>
				</div>
			</div>

			{/* Modal Đổi mật khẩu */}
			{isChangePassOpen && (
				<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
					<div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden text-gray-900 animate-in zoom-in duration-200">
						<div className="p-6">
							<div className="relative mb-6 text-center">
								{/* Khối văn bản căn giữa */}
								<div className="px-8">
									<h3 className="text-xl font-bold text-gray-900">Security</h3>
								</div>
								{/* Nút X đặt tuyệt đối ở góc phải */}
								<button 
									onClick={() => setIsChangePassOpen(false)}
									className="absolute right-0 top-0 text-gray-400 hover:text-red-500"
								>
									<XCircle size={24} />
								</button>
							</div>

							<form onSubmit={handleChangePassword} className="space-y-4">
								<div className="relative">
									{/* <label className="text-xs font-bold text-gray-500 uppercase ml-1">Current Password</label> */}
									<label className={`text font-semibold ml-1 ${curPassError? "text-red-500" : "text-gray-900" }`}>
										Current Password
									</label>
									<input
										type={showCurrentPass ? "text" : "password"}
										required
										value={passwords.current}
										onChange={(e) => {
											setPasswords({...passwords, current: e.target.value})
											if (curPassError) setCurPassError('');
										}}
										className={`w-full mt-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg outline-none transition-all ${
											curPassError
												? 'border-red-500 border-2 focus:border-red-500'
												: 'border-gray-300 border-2 focus:border-cyan-500'
										}`}
										placeholder="••••••••"
									/>
									<button
										type="button"
										onClick={() => setShowCurrentPass(!showCurrentPass)}
										className="absolute right-3 bottom-1 -translate-y-1/2 text-gray-400 hover:text-cyan-600 transition-colors"
									>
										{showCurrentPass ? <EyeOff size={18} /> : <Eye size={18} />}
									</button>
								</div>

								<div className="relative">
									<label className="font-semibold text-gray-900 ml-1">New Password</label>
									<input
										type={showNewPass ? "text" : "password"}
										required
										value={passwords.new}
										onChange={(e) => setPasswords({...passwords, new: e.target.value})}
										className="w-full mt-1 px-4 py-2 rounded-lg outline-none transition-all"
										placeholder="••••••••"
									/>
									<button
										type="button"
										onClick={() => setShowNewPass(!showNewPass)}
										className="absolute right-3 bottom-1 -translate-y-1/2 text-gray-400 hover:text-cyan-600 transition-colors"
									>
										{showNewPass ? <EyeOff size={18} /> : <Eye size={18} />}
									</button>
								</div>

								<button
									type="submit"
									disabled={isSaving}
									className="w-full bg-cyan-600 text-white font-semibold py-3 rounded-lg hover:bg-cyan-700 transition-colors flex items-center justify-center gap-2 mt-2"
								>
									{isSaving ? <Loader2 className="animate-spin" size={20} /> : <><Save size={18} /> Save Changes</>}
								</button>
							</form>
						</div>
					</div>
				</div>
			)}
		</header>
	);
}