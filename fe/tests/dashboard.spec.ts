import { test, expect } from '@playwright/test';

test.describe('Water Quality Dashboard - Toàn bộ luồng hiển thị', () => {

  test.beforeEach(async ({ page, context }) => {
    page.on('pageerror', err => console.log(`[REACT CRASH ERROR]: ${err.message}`));

    // Set Cookie đăng nhập
    await context.addCookies([
      { name: 'access_token', value: 'fake-token-user', url: 'http://localhost:3000' },
      { name: 'user_role', value: 'USER', url: 'http://localhost:3000' }
    ]);

    // 1. CATCH-ALL ROUTE
    await page.route('**/*', async (route, request) => {
      if (request.resourceType() === 'fetch' || request.resourceType() === 'xhr') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
      } else {
        await route.continue();
      }
    });

    // 2. MOCK API PROFILE
    await page.route('**/auth/me', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: '1', role: 'USER', fullName: 'Tester', email: 'test@gmail.com' }) });
    });

    // 3. MOCK API LỊCH SỬ DỰ ĐOÁN (Đầy đủ mô hình AI)
    await page.route('**/prediction/history*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            "id": "mock_1",
            "idSensor": "sensor_1",
            "Nhiệt độ": 29.4, "pH": 7.2, "DO": 6.8, "Độ dẫn": 120.0, "Độ kiềm": 95.0,
            "N-NO2": 0.03, "N-NH4": 0.1, "P-PO4": 0.2, "H2S": 0.0, "TSS": 12.1, "COD": 18.0,
            "Aeromonas tổng số": 120.0, "Coliform": 4300.0,
            "created_at": new Date().toISOString(),
            "prediction": { 
              "best_model": "RandomForest",
              "models": [{ "model": "RandomForest", "accuracy": 0.94 }],
              "summary": {
                "wqi": { "score": 85, "label": "Good" },
                "risk": { "status": "Low Risk", "level": 0 },
                "forecast_24h": { "trend": "Stable", "predicted_wqi_range": [80, 90], "model_used": "RandomForest" },
                "confidence": 92.5
              }
            } 
          }
        ])
      });
    });

    // 4. MOCK API CLASSIFICATION
    await page.route('**/api/v1/sensors/classification*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
            "overall_quality": "Good Water",
            "hardness": { "category": "Moderately Hard", "value_mgl": 102.0 },
            "salinity": { "level": "Slightly Saline" },
            "alkalinity": { "level": "Moderate" },
            "temperature": { "status": "Safe" },
            "ph": 7.2, "do": 6.8
        })
      });
    });

    // 5. MOCK API TRENDS (Biểu đồ xu hướng)
    await page.route('**/api/analytics/trends*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
            "phTrend": [{ "time": "08:00", "value": 7.1 }, { "time": "12:00", "value": 7.2 }],
            "temperatureTrend": [{ "time": "08:00", "value": 28.5 }, { "time": "12:00", "value": 29.4 }],
            "dissolvedOxygenTrend": [{ "time": "08:00", "value": 6.9 }, { "time": "12:00", "value": 6.8 }],
            "conductivityTrend": [],
            "turbidityComparison": []
        })
      });
    });

    // 6A. MOCK API CÀI ĐẶT EMAIL ALERTS
    await page.route('**/api/v1/alerts/settings/email', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ enabled: true }) });
    });

    // 6B. MOCK API DANH SÁCH ALERTS
    await page.route('**/api/v1/alerts*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            "id": "alert_1",
            "level": "Critical",
            "message": "Nồng độ DO giảm mạnh, nguy cơ thiếu oxy cho thuỷ sản",
            "time_ago": "5 phút trước",
            "wqi_score": 28,
            "contamination_risk": "Cao"
          },
          {
            "id": "alert_2",
            "level": "Warning",
            "message": "Nhiệt độ nước vượt ngưỡng 32°C",
            "time_ago": "1 giờ trước",
            "wqi_score": 45,
            "contamination_risk": "Trung bình"
          }
        ])
      });
    });

    // 7. MOCK API BẢN ĐỒ (MAP VISUALIZATION)
    await page.route('**/api/sensors*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            { 
              "_id": "sensor_1", 
              "sensorName": "Trạm Quan Trắc A - Vùng Ven", 
              "location": { "latitude": 10.8231, "longitude": 106.6297 }, 
              "status": "ONLINE",
              "isDeleted": false
            },
            { 
              "_id": "sensor_2", 
              "sensorName": "Trạm Quan Trắc B - Nước Sâu", 
              "location": { "latitude": 10.7626, "longitude": 106.6601 }, 
              "status": "OFFLINE",
              "isDeleted": false
            }
          ]
        })
      });
    });

    // Bắt đầu truy cập
    await page.goto('/');
  });

  test('Giao diện Dashboard render thành công tất cả Component', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Real-Time Sensor Readings/i })).toBeVisible({ timeout: 15000 });

    // Kiểm tra Sensor Cards
    await expect(page.getByText('pH Value')).toBeVisible();
    await expect(page.getByText('7.2', { exact: true })).toBeVisible();

    // Kiểm tra AI Panel
    await expect(page.getByText('Water Quality Index (WQI)')).toBeVisible();
    await expect(page.getByText('85', { exact: true })).toBeVisible();

    // KIỂM TRA MAP VISUALIZATION ĐÃ CÓ DATA
    await expect(page.getByText('Trạm Quan Trắc A - Vùng Ven')).toBeVisible();
    await expect(page.getByText('Trạm Quan Trắc B - Nước Sâu')).toBeVisible();

    // KIỂM TRA ALERTS PANEL ĐÃ CÓ DATA
    await expect(page.getByText('Nồng độ DO giảm mạnh, nguy cơ thiếu oxy cho thuỷ sản')).toBeVisible();
    await expect(page.getByText('Critical').first()).toBeVisible();
    await expect(page.getByText('Warning').first()).toBeVisible();
  });
});