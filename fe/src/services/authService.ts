// src/services/authService.ts

import api from './api';

export const authService = {
    /**
     * Đăng nhập người dùng
     * Trả về: role của user nếu thành công, null nếu thất bại
     */
    login: async (email: string, password: string): Promise<string | null> => {
        try {
            const response = await api.post('/auth/login', { email, password });
            
            const { access_token, user } = response.data;

            if (access_token) {
                // Lưu Token và Role vào Cookie để dùng cho các request và phân quyền frontend
                document.cookie = `access_token=${access_token}; path=/; max-age=3600; SameSite=Lax`;
                document.cookie = `user_role=${user.role}; path=/; max-age=3600; SameSite=Lax`;
                return user.role;
            }
            return null;
        } catch (error) {
            console.error("Login failed:", error);
            return null;
        }
    },

    /**
     * Đăng ký tài khoản mới
     * Trả về: role của user sau khi đăng ký thành công, null nếu thất bại
     */
    register: async (userData: any): Promise<string | null> => {
        try {
            const response = await api.post('/auth/register', userData);
            const { token, user } = response.data;

            if (token) {
                document.cookie = `access_token=${token}; path=/; max-age=3600; SameSite=Lax`;
                document.cookie = `user_role=${user.role}; path=/; max-age=3600; SameSite=Lax`;
                return user.role;
            }
            return null;
        } catch (error) {
            console.error("Registration failed:", error);
            return null;
        }
    },

    /**
     * Đăng xuất người dùng
     */
    logout: async () => {
        try {
            // Gọi API logout để backend xử lý (nếu có logic hủy session/token)
            await api.post('/auth/logout');
        } catch (error) {
            console.error("Logout API call failed:", error);
        } finally {
            // Luôn xóa cookie và chuyển hướng về trang login dù API có lỗi hay không
            document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
            document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
            window.location.href = '/login';
        }
    },

    /**
     * Kiểm tra trạng thái đăng nhập dựa trên sự tồn tại của access_token
     */
    isAuthenticated: (): boolean => {
        return document.cookie
            .split(';')
            .some((item) => item.trim().startsWith('access_token='));
    },

    /**
     * Lấy role hiện tại của người dùng từ cookie
     */
    getUserRole: (): string | null => {
        const roleCookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('user_role='));
        return roleCookie ? roleCookie.split('=')[1] : null;
    },

    /**
     * Kiểm tra nhanh xem người dùng hiện tại có phải Admin không
     */
    isAdmin: (): boolean => {
        return authService.getUserRole() === 'ADMIN';
    }
};