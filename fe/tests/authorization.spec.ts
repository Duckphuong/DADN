import { test, expect } from '@playwright/test';

test.describe('Kiểm tra Phân quyền & Chuyển hướng URL (Authorization & Routing)', () => {

  test.describe('1. Khách (Chưa đăng nhập / Không có Token)', () => {
    
    test('Gõ URL Dashboard (/) -> Bị đẩy về /login', async ({ page }) => {
      await page.goto('/');
      await expect(page).toHaveURL(/.*\/login/);
    });

    test('Gõ URL Admin (/admin) -> Bị đẩy về /login', async ({ page }) => {
      await page.goto('/admin');
      await expect(page).toHaveURL(/.*\/login/);
    });
    
    test('Gõ URL lạ không tồn tại (/duong-dan-la) -> Bị đẩy về /login', async ({ page }) => {
      await page.goto('/duong-dan-la');
      await expect(page).toHaveURL(/.*\/login/);
    });
  });

  test.describe('2. Tài khoản USER (Đã đăng nhập)', () => {
    test.beforeEach(async ({ context }) => {
      await context.addCookies([
        { name: 'access_token', value: 'fake-token-user', url: 'http://localhost:3000' },
        { name: 'user_role', value: 'USER', url: 'http://localhost:3000' }
      ]);
    });

    test('Gõ URL Dashboard (/) -> Truy cập thành công', async ({ page }) => {
      await page.route('**/api/v1/sensors/latest', async route => route.fulfill({ status: 200, body: '{}' }));
      
      await page.goto('/');
      await expect(page).toHaveURL('http://localhost:3000/');
    });

    test('Cố tình gõ URL Admin (/admin) -> Bị đẩy ra trang login', async ({ page }) => {
      await page.goto('/admin');
      await expect(page).toHaveURL(/.*\/login/); 
    });

    test('Gõ URL lạ không tồn tại (/xyz-abc) -> Chuyển về lại trang dashboard', async ({ page }) => {
      await page.goto('/xyz-abc');
      await expect(page).toHaveURL('/'); 
    });
  });

  test.describe('3. Tài khoản ADMIN (Đã đăng nhập)', () => {
    test.beforeEach(async ({ context }) => {
      await context.addCookies([
        { name: 'access_token', value: 'fake-token-admin', url: 'http://localhost:3000' },
        { name: 'user_role', value: 'ADMIN', url: 'http://localhost:3000' }
      ]);
    });

    test('Gõ URL Admin (/admin) -> Truy cập thành công', async ({ page }) => {
      await page.route('**/auth/users', async route => route.fulfill({ status: 200, body: '[]' }));
      await page.goto('/admin');
      await expect(page).toHaveURL('http://localhost:3000/admin');
    });

    test('Cố tình gõ URL Dashboard (/) -> Bị chặn (Nếu Admin không được vào)', async ({ page }) => {
      await page.goto('/');
      await expect(page).toHaveURL(/.*\/login/);
    });

    test('Gõ URL lạ không tồn tại (/xyz-abc) -> Chuyển về lại trang admin', async ({ page }) => {
      await page.goto('/xyz-abc');
      await expect(page).toHaveURL('/admin'); 
    });
  });
});