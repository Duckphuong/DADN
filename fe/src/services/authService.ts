// src/services/authService.ts

export const authService = {
    /**
     * Hàm đăng nhập: Trả về role của user nếu thành công, ngược lại trả về null
     */
    login: async (email: string, password: string): Promise<string | null> => {
        // Giả lập delay gọi API
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // --- CẤU HÌNH TÀI KHOẢN MẪU (Demo) ---
        const users = [
            { email: 'admin@gmail.com', password: '123', role: 'admin' },
            { email: 'abc@gmail.com', password: '123', role: 'user' }
        ];
        // ------------------------------------

        const user = users.find(u => u.email === email && u.password === password);

        if (user) {
            // Lưu session chung
            document.cookie = 'user_session=true; path=/; max-age=3600; SameSite=Lax';
            // Lưu role riêng để phân quyền giao diện
            document.cookie = `user_role=${user.role}; path=/; max-age=3600; SameSite=Lax`;
            
            return user.role;
        }

        return null;
    },

    /**
     * Đăng xuất: Xóa sạch các cookie liên quan
     */
    logout: () => {
        document.cookie = 'user_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
        document.cookie = 'user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
        window.location.href = '/login';
    },

    /**
     * Kiểm tra đã đăng nhập hay chưa
     */
    isAuthenticated: (): boolean => {
        return document.cookie
            .split(';')
            .some((item) => item.trim().startsWith('user_session='));
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
     * Kiểm tra nhanh xem có phải Admin không
     */
    isAdmin: (): boolean => {
        return authService.getUserRole() === 'admin';
    }
};