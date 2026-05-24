import { test, expect } from '@playwright/test';

test.describe('Admin Dashboard - Quản lý Users', () => {
  
  // Khởi tạo mock data
  const initialUsers = [
    { id: '1', fullName: 'Hanah', email: 'hanah@gmail.com', role: 'ADMIN', status: 'ACTIVE', phoneNumber: '1234567890' },
    { id: '2', fullName: 'Olala', email: 'olala@gmail.com', role: 'USER', status: 'ACTIVE', phoneNumber: '0123456789' }
  ];

  test.beforeEach(async ({ page, context }) => {
    await context.addCookies([
      { name: 'access_token', value: 'fake-admin-token', url: 'http://localhost:3000' },
      { name: 'user_role', value: 'ADMIN', url: 'http://localhost:3000' }
    ]);
  });

  test('Hiển thị danh sách User từ API', async ({ page }) => {
    await page.route('**/auth/users', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(initialUsers) });
    });

    await page.goto('/admin');
    
    await expect(page.getByText('Hanah')).toBeVisible();
    await expect(page.getByText('Olala')).toBeVisible();
  });

  test('Thêm User mới (Create) gọi đúng API và cập nhật UI', async ({ page }) => {
    // 1. Mock API Get All
    await page.route('**/auth/users', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(initialUsers) });
    });

    // 2. Mock API Register/Create
    await page.route('**/auth/register', async (route) => {
      const postData = JSON.parse(route.request().postData() || '{}');
      expect(postData.email).toBe('newuser@gmail.com');
      
      await route.fulfill({ status: 201, body: JSON.stringify({ message: "Success", user: { id: '3', role: 'USER' } }) });
    });

    await page.goto('/admin');
    await page.getByRole('button', { name: /Add New User|Thêm/i }).click();

    // Điền form
    await page.getByLabel(/Full Name/i).fill('ThisIsNewUser');
    await page.getByLabel(/Email Address/i).fill('newuser@gmail.com');
    await page.getByLabel(/Phone Number/i).fill('0911111111');
    await page.getByLabel(/Role/i).selectOption('USER');
    
    // Khi bấm save, thay đổi mock data của route GET để mô phỏng việc UI gọi lại API (Refetch)
    await page.route('**/auth/users', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify([...initialUsers, { id: '3', fullName: 'ThisIsNewUser', email: 'newuser@gmail.com', role: 'USER', status: 'ACTIVE' }]) });
    }, { times: 1 }); // Chỉ áp dụng route này 1 lần (override route cũ)

    await page.getByRole('button', { name: 'Save' }).click();

    // Modal đóng và hiển thị người dùng mới
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.getByText('ThisIsNewUser')).toBeVisible();
  });

  test('Cập nhật User (Edit) thành công', async ({ page }) => {
    await page.route('**/auth/users', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(initialUsers) });
    });

    // Mock API gọi chi tiết User để fill vào form Edit
    await page.route('**/auth/users/2', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ status: 200, body: JSON.stringify(initialUsers[1]) });
      } else if (route.request().method() === 'PATCH') {
        await route.fulfill({ status: 200, body: JSON.stringify({ message: "Updated" }) });
      }
    });

    await page.goto('/admin');

    // Bấm nút Edit của user thứ 2
    const editButton = page.locator('tr').filter({ hasText: 'Olala' }).getByTitle(/Edit|Sửa/i);
    await editButton.click();

    // Sửa trạng thái
    await page.getByLabel(/Status/i).selectOption('INACTIVE');
    
    // Mock lại list sau khi update
    await page.route('**/auth/users', async (route) => {
        const updatedUsers = [...initialUsers];
        updatedUsers[1].status = 'INACTIVE';
        await route.fulfill({ status: 200, body: JSON.stringify(updatedUsers) });
    });

    await page.getByRole('button', { name: 'Save' }).click();

    // Xác nhận UI cập nhật thành INACTIVE
    const userRow = page.locator('tr').filter({ hasText: 'Olala' });
    await expect(userRow.getByText('INACTIVE')).toBeVisible();
  });

  test('Xóa User (Delete) thành công', async ({ page }) => {
    await page.route('**/auth/users', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(initialUsers) });
    });

    await page.route('**/auth/users/2', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 200, body: JSON.stringify({ message: "Deleted" }) });
      }
    });

    await page.goto('/admin');

    // Chấp nhận dialog confirm của browser
    page.on('dialog', async dialog => await dialog.accept());

    // Cài đè lại route get All sau khi xoá
    await page.route('**/auth/users', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify([initialUsers[0]]) });
    });

    const deleteButton = page.locator('tr').filter({ hasText: 'Olala' }).getByTitle(/Remove|Xóa/i);
    await deleteButton.click();
    
    // Xác nhận user đã biến mất
    await expect(page.getByText('Olala')).not.toBeVisible();
  });
});