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
    XCircle
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
  const [isForgotModalOpen, setIsForgotModalOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [isSendingReset, setIsSendingReset] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    setEmailError('');
    setPasswordError('');
    let hasError = false;

    // 1. Kiểm tra Email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      setEmailError('Email is required.');
      hasError = true;
    } else if (!emailRegex.test(email)) {
      setEmailError('Invalid email.');
      hasError = true;
    }

    // 2. Kiểm tra Password bỏ trống
    if (!password) {
      setPasswordError('Password is required.');
      hasError = true;
    }

    if (hasError) return;

    // 3. Tiến hành gọi API nếu dữ liệu hợp lệ
    setIsLoading(true);
    try {
      const role = await authService.login(email, password);

      if (role === 'ADMIN') {
        navigate('/admin');
      } else if (role === 'USER') {
        navigate('/');
      } else {
        setPasswordError('Wrong password');
      }
    } catch (err) {
      setError('Something went wrong. Please try again later.');
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
                <div className="flex items-center justify-center border-b-2 border-white rounded-b-full">
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
                {emailError ? 'Invalid Email Address' : 'Email Address'}
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
                  className={`login-input-field ${
                    emailError
                      ? 'border-red-500 border-2 focus:border-red-500'
                      : 'border-gray-300 border-2 focus:border-cyan-500'
                  }`}
                  style={
                    emailError
                      ? { borderColor: '#dc2626' }
                      : {}
                  }
                  placeholder="abc@gmail.com"
                />
                <Mail className={`absolute ${emailError ? 'text-red-500' : ''}`} size={18} />
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
                      : 'border-gray-300 border-2 focus:border-cyan-500'
                  }`}
                />
                <Lock
                  className={`absolute ${passwordError ? 'text-red-500' : ''}`}
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
              <button
                type="button" // Quan trọng: tránh submit form chính
                onClick={() => setIsForgotModalOpen(true)}
                className="text-cyan-600 hover:underline bg-transparent border-none p-0 cursor-pointer text-sm font-medium transition-all"
              >
                Forgot password?
              </button>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="login-submit-btn hover:scale-101"
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

      {/* Modal Quên mật khẩu */}
      {isForgotModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6">
              <div className="relative mb-6 text-center">
                {/* Khối văn bản căn giữa */}
                <div className="px-8">
                  <h3 className="text-xl font-bold text-gray-900">Reset Password</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Enter your email and we'll send you a reset link.
                  </p>
                </div>

                {/* Nút X đặt tuyệt đối ở góc phải */}
                <button 
                  onClick={() => setIsForgotModalOpen(false)}
                  className="absolute right-0 top-0 text-gray-400 hover:text-red-500"
                >
                  <XCircle size={24} />
                </button>
              </div>

              <form onSubmit={async (e) => {
                e.preventDefault();
                setIsSendingReset(true);
                // Giả lập gọi API gửi mail
                setTimeout(() => {
                  alert(`Reset link sent to: ${resetEmail}`);
                  setIsSendingReset(false);
                  setIsForgotModalOpen(false);
                }, 1500);
              }}>
                <div className="space-y-4">
                  <div className="relative text-sm">
                    <input
                      type="email"
                      required
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="example@gmail.com"
                      className="w-full px-9 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-cyan-500 outline-none transition-all"
                    />
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={isSendingReset}
                    className="text-sm w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-semibold py-3 rounded-xl hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                  >
                    {isSendingReset ? (
                      <Loader2 className="animate-spin" size={20} />
                    ) : (
                      <>
                        <span>Send Reset Link</span>
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
            
            <div className="bg-gray-50 p-4 text-center border-t border-gray-100">
              <button 
                onClick={() => setIsForgotModalOpen(false)}
                className="text-sm text-gray-600 hover:text-gray-900 font-medium"
              >
                Back to login
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
