import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('Người dùng bình thường (USER) đăng nhập thành công', async ({ page }) => {
    // 1. Mock API Login trả về quyền USER
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          access_token: 'fake-jwt-token-user', 
          user: { role: 'USER', email: 'user@gmail.com' } 
        })
      });
    });

    // 2. Truy cập trang login
    await page.goto('/login');

    // 3. Điền form
    await page.getByPlaceholder('abc@gmail.com').fill('user@gmail.com');
    await page.getByPlaceholder('•••••').fill('password123');
    
    // 4. Bấm nút Sign In
    await page.getByRole('button', { name: 'Sign In' }).click();

    // 5. Kiểm tra chuyển hướng về trang chủ/Dashboard
    await expect(page).toHaveURL('/'); 
  });

  test('Quản trị viên (ADMIN) đăng nhập thành công', async ({ page }) => {
    // 1. Mock API Login trả về quyền ADMIN
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          access_token: 'fake-jwt-token-admin', 
          user: { role: 'ADMIN', email: 'admin@gmail.com' } 
        })
      });
    });

    await page.goto('/login');

    await page.getByPlaceholder('abc@gmail.com').fill('admin@gmail.com');
    await page.getByPlaceholder('•••••').fill('admin_password');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Kiểm tra chuyển hướng vào trang admin
    await expect(page).toHaveURL(/.*\/admin/);
  });
});