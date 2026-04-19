# Backend

---

## Tính năng (Features)

- Đăng ký, đăng nhập, đăng xuất bằng **JWT**.
- Quản lý người dùng cho **Admin**.
- Lưu trữ người dùng (User) và trạm cảm biến (Sensor Station) trong **MongoDB**.
- Chỉ chủ sở hữu (**Owner**) mới được quyền đọc, sửa, xóa dữ liệu của mình.
- Xóa mềm (**Soft delete**) cho bộ sưu tập `sensor_informations`.
- Xóa mềm người dùng bằng cách chuyển `status` sang `INACTIVE`.
- Thời gian (Datetime) được chuẩn hóa theo múi giờ **UTC**.
- Phản hồi lỗi (Error response) được chuẩn hóa theo một định dạng duy nhất.

### Alert Service (Dịch vụ cảnh báo)

**Mô tả:** Hệ thống cảnh báo tự động gửi email khi chất lượng nước xuống cấp nghiêm trọng.

**Cách hoạt động:**
1. **Giám sát tự động:** Mỗi phút hệ thống quét các dự đoán AI chưa xử lý
2. **Điều kiện kích hoạt:** WQI < 50 hoặc rủi ro ô nhiễm "High Risk"/"Critical"
3. **Chống spam:** Đợi 2 giờ cho cảnh báo không nghiêm trọng, gửi ngay cho trường hợp khẩn cấp
4. **Gửi email:** Thông báo chi tiết về tình trạng nước qua SMTP Gmail

**API Endpoints:**
- `GET /api/v1/alerts` - Lấy danh sách cảnh báo (Critical/Warning/Info)
- `PUT /api/v1/alerts/{id}/read` - Đánh dấu đã đọc

**Cấu hình Email:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL=your-email@gmail.com
PASSWORD=your-app-password
ALERT_EMAIL_TO=recipient@example.com
```

---

## Công nghệ sử dụng (Tech Stack)

- **Ngôn ngữ:** Python 3.10+
- **Framework:** Flask 3.1
- **Tiện ích:** Flask-CORS, PyJWT, bcrypt, APScheduler
- **Database:** MongoDB
- **Email:** SMTP (Gmail)

---

## Cấu trúc dự án (Project Structure)

```text
be/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── bootstrap/
│   │   └── container.py
│   ├── domain/
│   │   ├── auth/
│   │   ├── sensor_station/
│   │   ├── prediction/          # Alert service domain
│   │   └── shared/
│   ├── application/
│   │   ├── auth/
│   │   ├── sensor_station/
│   │   └── common/
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   └── mongo/
│   │   └── security/
│   ├── presentation/
│   │   └── http/
│   │       ├── middleware/
│   │       ├── routes/
│   │       ├── serializers/
│   │       └── validators/
│   ├── routes/
│   │   ├── alert_routes.py      # Alert API endpoints
│   │   └── prediction_routes.py
│   └── services/
│       ├── ai_model_service.py
│       └── alert_service.py     # Email alert service
├── requirements.txt
├── run.py
└── README.md
```

---

## Trách nhiệm của các lớp (Layer Responsibilities)

### `domain/`

- Chứa thực thể (entity), đối tượng giá trị (value object), các quy tắc nghiệp vụ (domain rules).

### `application/`

- Chứa các trường hợp sử dụng (use case) và điều phối luồng nghiệp vụ.
- Định nghĩa giao diện (interfaces) cho repository và các cổng bảo mật (security ports).

### `infrastructure/`

- Kết nối MongoDB, triển khai Repository và Document mapper.
- Chứa các dịch vụ hạ tầng: JWT service, Password hasher.

### `presentation/`

- Flask routes, Request validation và Middleware HTTP.
- Chuyển đổi dữ liệu phản hồi (Serializer).
- Ánh xạ lỗi từ application exception sang mã trạng thái HTTP.

---

## Cài đặt và Chạy ( Đang test trên Ubuntu , Ai làm Win sửa lại nha)

```bash
cd /home/dungne/DADN/be
# python3 -m venv .venv
python -m venv .venv

# source .venv/bin/activate
source .venv/Scripts/activate
pip install -r requirements.txt
# python3 run.py
python run.py

```

- **Mặc định:** `http://127.0.0.1:5000`
- **Kiểm tra nhanh:** `curl http://127.0.0.1:5000/health`

---

## Danh sách API (API Summary)

### 1. Hệ thống & Xác thực

- `GET /health`: Kiểm tra trạng thái hệ thống.
- `POST /auth/register`: Đăng ký tài khoản.
- `POST /auth/login`: Đăng nhập lấy JWT.
- `POST /auth/logout`: Đăng xuất (Stateless).
- `GET /auth/me`: Lấy thông tin người dùng hiện tại.

### 2. Quản lý người dùng (Cần role `ADMIN`)

- `GET /auth/users`: Lấy danh sách toàn bộ người dùng.
- `GET /auth/users/<id>`: Xem chi tiết người dùng.
- `PATCH /auth/users/<id>`: Cập nhật `fullName`, `phoneNumber`, `urlAvatar`, `role`, `status`.
- `DELETE /auth/users/<id>`: Xóa mềm người dùng bằng cách chuyển `status` sang `INACTIVE`.

### 3. Trạm cảm biến (Cần Authorization Header)

- `POST /api/sensors`: Tạo trạm mới.
- `GET /api/sensors`: Lấy danh sách (Phân trang: `page`, `limit`).
- `GET /api/sensors/<id>`: Xem chi tiết.
- `PATCH /api/sensors/<id>`: Cập nhật từng phần.
- `DELETE /api/sensors/<id>`: Xóa mềm.

---

## Định dạng phản hồi lỗi

Tất cả lỗi đều tuân theo format:

```json
{
    "error": "Nội dung thông báo lỗi chi tiết"
}
```

## Hướng dẫn phát triển (Development Guide)

Khi thêm tính năng mới, hãy tuân theo trình tự:

1. Thêm entity tại `app/domain/`.
2. Thêm use case và interface tại `app/application/`.
3. Triển khai repository tại `app/infrastructure/`.
4. Thêm validator, serializer và route tại `app/presentation/`.
5. Đăng ký dependencies tại `app/bootstrap/container.py`.

```

```

## ERD
link erd: https://drive.google.com/file/d/1K8EVtyi5xTBa0v6GMxgX_m5VM2c7QnFi/view?usp=sharing
