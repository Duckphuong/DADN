// src/components/LoginPage.tsx
import React, { useState } from 'react';
import {
    ArrowRight,
    Mail,
    Lock,
    Loader2,
    Droplets,
    AlertCircle,
    Eye,
    EyeOff,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

export function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [emailError, setEmailError] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();

        setEmailError('');
        setPasswordError('');
        let hasError = false;

        // 1. Kiểm tra Email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) {
            setEmailError('Vui lòng nhập địa chỉ email.');
            hasError = true;
        } else if (!emailRegex.test(email)) {
            setEmailError('Email bạn đã nhập không đúng định dạng.');
            hasError = true;
        }

        // 2. Kiểm tra Password bỏ trống
        if (!password) {
            setPasswordError('Vui lòng nhập mật khẩu.');
            hasError = true;
        }

        if (hasError) return;

        // 3. Tiến hành gọi API nếu dữ liệu hợp lệ
        setIsLoading(true);
        try {
            const role = await authService.login(email, password);

            if (role === 'admin') {
                navigate('/admin');
            } else if (role === 'user') {
                navigate('/');
            } else {
                setPasswordError('Mật khẩu bạn đã nhập không chính xác.');
            }
        } catch (err) {
            setError('Lỗi hệ thống, vui lòng thử lại sau.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-page-wrapper">
            <div className="login-card">
                <div className="login-content-inner">
                    {/* Khu vực Logo */}
                    <div className="login-logo-area">
                        <div
                            style={{
                                background:
                                    'linear-gradient(90deg, #0092b8, #155dfc)',
                            }}
                            className="flex items-center justify-center w-[72px] h-[72px] rounded-2xl p-3 shadow-sm"
                        >
                            <div className="w-12 h-12 rounded-full flex items-center justify-center relative">
                                <div className="flex items-center justify-center w-full h-full border-b-2 border-white rounded-b-full">
                                    <Droplets
                                        className="absolute text-white"
                                        size={50}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Tiêu đề Welcome */}
                    <div className="login-welcome-title">
                        <h2
                            style={{
                                margin: 0,
                                fontSize: '24px',
                                fontWeight: 'bold',
                            }}
                        >
                            Welcome Back
                        </h2>
                    </div>

                    {/* Mô tả phụ */}
                    <div className="login-subtitle">
                        <p
                            style={{ margin: 0, lineHeight: '24px' }}
                            className="text-center"
                        >
                            Sign in to access the Water Quality Monitoring
                            Dashboard
                        </p>
                    </div>

                    {/* Form chính */}
                    <form
                        onSubmit={handleLogin}
                        className="login-form-container"
                    >
                        {/* Email Field */}
                        <div className="login-input-group">
                            <label
                                className={`font-medium ${emailError ? 'text-red-500' : ''}`}
                            >
                                Email Address
                            </label>
                            <div
                                className="login-input-wrapper"
                                style={{ position: 'relative' }}
                            >
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => {
                                        setEmail(e.target.value);
                                        if (emailError) setEmailError('');
                                    }}
                                    className={`login-input-field ${emailError ? 'border-red-500' : ''}`}
                                    style={
                                        emailError
                                            ? { borderColor: '#dc2626' }
                                            : {}
                                    }
                                    placeholder="abc@gmail.com"
                                />
                                <Mail className="absolute" size={18} />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div className="login-input-group">
                            <label
                                className={`font-medium ${passwordError ? 'text-red-500' : ''}`}
                            >
                                {passwordError ? 'Wrong password' : 'Password'}
                            </label>

                            <div className="login-input-wrapper relative">
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => {
                                        setPassword(e.target.value);
                                        if (passwordError) setPasswordError('');
                                    }}
                                    placeholder="•••••"
                                    className={`login-input-field w-full outline-none transition-colors ${
                                        passwordError
                                            ? 'border-red-500 border-2 focus:border-red-500'
                                            : 'border-gray-300'
                                    }`}
                                />
                                <Lock
                                    className={`absolute left-3 top-1/2 -translate-y-1/2 ${passwordError ? 'text-red-500' : 'text-gray-400'}`}
                                    size={18}
                                />
                            </div>
                        </div>

                        {/* Remember Me & Forgot Password */}
                        <div
                            style={{
                                display: 'flex',
                                width: '100%',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}
                        >
                            <div
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                }}
                            >
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded"
                                />
                                <span style={{ fontSize: '14px' }}>
                                    Remember me
                                </span>
                            </div>
                            <div
                                style={{ fontSize: '14px', fontWeight: '500' }}
                            >
                                <a
                                    href="#"
                                    style={{
                                        color: '#0092b8',
                                        textDecoration: 'none',
                                    }}
                                    className="hover:underline"
                                >
                                    Forgot password?
                                </a>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="login-submit-btn"
                        >
                            {isLoading ? (
                                <Loader2 className="animate-spin" size={20} />
                            ) : (
                                <>
                                    <span>Sign In</span>
                                    <ArrowRight size={16} />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer của Card */}
                <div className="login-footer">
                    <p style={{ margin: 0,
                                justifyContent: 'center',
                                alignItems: 'center',
                            }}>
                        System requires authorized personnel access.
                    </p>
                </div>
            </div>
        </div>
    );
}
