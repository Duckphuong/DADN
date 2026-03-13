// src/services/authService.ts

export const authService = {
    login: async (email: string, password: string): Promise<boolean> => {
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // --- CHANGE THESE TWO LINES ---
        const validEmail = 'abc@gmail.com';
        const validPassword = '123';
        // ------------------------------

        if (email === validEmail && password === validPassword) {
            document.cookie =
                'user_session=true; path=/; max-age=3600; SameSite=Lax';
            return true;
        }
        return false;
    },

    logout: () => {
        // Clear the cookie by setting expiry to the past
        document.cookie =
            'user_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
        window.location.href = '/login';
    },

    isAuthenticated: (): boolean => {
        return document.cookie
            .split(';')
            .some((item) => item.trim().startsWith('user_session='));
    },
};
