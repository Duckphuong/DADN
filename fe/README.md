# 🌊 Water Quality Monitoring Dashboard (AI-Powered)

Tài liệu này hướng dẫn chi tiết cách thiết lập, khởi chạy giao diện người dùng (Frontend) và thực thi các kịch bản kiểm thử tự động (E2E Testing) cho dự án Giám sát Chất lượng Nước.

---

## 🚀 1. Hướng dẫn cài đặt và chạy Frontend (Local)

Sau khi đã clone repository về máy cá nhân, bạn thực hiện các bước sau để khởi chạy giao diện:

1. **Di chuyển vào thư mục Frontend:**
   Mở terminal và trỏ đường dẫn vào thư mục chứa mã nguồn frontend:
   ```bash
   cd fe
   ```

2. **Cài đặt các thư viện phụ thuộc (Dependencies):**
   Dự án sử dụng môi trường ReactJS, TypeScript và Vite. Chạy lệnh sau để tải toàn bộ thư viện cần thiết:
   ```bash
   npm install
   ```

3. **Khởi động server phát triển (Development Server):**
   ```bash
   npm run dev
   ```

4. **Truy cập ứng dụng:**
   Mở trình duyệt web và truy cập vào địa chỉ được hiển thị trên terminal (thường là `http://localhost:3000` hoặc `http://localhost:5173`).

---

## 🧪 2. Hướng dẫn chạy Test (E2E với Playwright)

Dự án sử dụng Playwright để kiểm thử tự động các luồng chức năng thực tế như Xác thực (Đăng nhập), Phân quyền và hiển thị Dữ liệu Dashboard. 

Để chạy test, hãy chắc chắn rằng bạn đang đứng ở thư mục frontend (chứa file `playwright.config.ts`) và đã hoàn thành lệnh `npm install` ở phần trên.

1. **Cài đặt trình duyệt cho Playwright (Chỉ làm ở lần đầu tiên):**
   Playwright cần cài đặt các môi trường trình duyệt cốt lõi (Chromium, Firefox, WebKit) để chạy giả lập.
   ```bash
   npx playwright install
   ```

2. **Thực thi toàn bộ Testcases:**
   Lệnh này sẽ quét và chạy tự động tất cả các kịch bản kiểm thử (các file `.spec.ts` trong thư mục `tests`).
   ```bash
   npx playwright test
   ```

3. **Xem Báo cáo kiểm thử (Test Report):**
   Sau khi luồng kiểm thử hoàn tất, để xem kết quả chi tiết dưới dạng giao diện web (đặc biệt hữu ích để debug khi có test bị fail), hãy chạy lệnh:
   ```bash
   npx playwright show-report
   ```

> **💡 Lưu ý:** Toàn bộ các file test E2E của dự án đã được tích hợp sẵn cơ chế Mock API (Giả lập phản hồi từ Backend). Do đó, bạn hoàn toàn có thể chạy test độc lập cho Frontend thành công mà không cần phải khởi chạy Backend thực tế.