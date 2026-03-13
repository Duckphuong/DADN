# Water Quality Monitoring System

Dự án hệ thống giám sát chất lượng nước sử dụng trí tuệ nhân tạo (AI) để dự đoán và phân tích dữ liệu từ các cảm biến. Hệ thống bao gồm backend (Flask) và frontend (React/Vite) để thu thập, xử lý và hiển thị dữ liệu chất lượng nước.

## Cấu trúc dự án

- `be/`: Backend Python Flask
    - `app/`: Mã nguồn ứng dụng
        - `routes/`: Các endpoint API
        - `services/`: Logic xử lý (AI, sensor, alert)
        - `models/`: Mô hình dữ liệu
        - `database/`: Cấu hình database
    - `run.py`: File khởi chạy server
    - `requirements.txt`: Dependencies Python
- `fe/`: Frontend React/Vite
    - `src/`: Mã nguồn React
    - `package.json`: Dependencies Node.js

## Cài đặt và chạy

### Backend

1. Di chuyển vào thư mục backend:
    ```
    cd be
    ```
2. Cài đặt dependencies:
    ```
    pip install -r requirements.txt
    ```
3. Khởi chạy server:

    ```
    python run.py
    ```

    Server sẽ chạy trên `http://127.0.0.1:5000`.

4. Xem db
    ```
    python check_db.py
    ```

### Frontend

1. Di chuyển vào thư mục frontend:
    ```
    cd fe
    ```
2. Cài đặt dependencies:
    ```
    npm install
    ```
3. Khởi chạy development server:
    ```
    npm run dev
    ```
    Frontend sẽ chạy trên `http://localhost:3000` (hoặc port khác nếu bị chiếm).

## API Documentation

Hệ thống cung cấp các API AI chính cho dự đoán và lịch sử. Tất cả API đều sử dụng JSON.

### 1. Prediction API

Dự đoán chất lượng nước dựa trên các thông số cảm biến.

- **Endpoint**: `POST /prediction/predict`
- **Mô tả**: Nhận dữ liệu các thông số nước và trả về kết quả dự đoán chất lượng.
- **Request Body** (JSON):

    ```json
    {
        "Temp": 67.45,
        "Turbidity": 10.13,
        "DO": 0.208,
        "BOD": 7.474,
        "CO2": 10.181,
        "pH": 4.752,
        "Alkalinity": 218.365,
        "Hardness": 300.125,
        "Calcium": 337.178,
        "Ammonia": 0.286,
        "Nitrite": 4.355,
        "Phosphorus": 0.006,
        "H2S": 0.067,
        "Plankton": 6070
    }
    ```

- **Ví dụ curl**:

    ```bash
    curl -X POST http://127.0.0.1:5000/prediction/predict \
    -H "Content-Type: application/json" \
    -d '{
        "Temp": 67.45,
        "Turbidity": 10.13,
        "DO": 0.208,
        "BOD": 7.474,
        "CO2": 10.181,
        "pH": 4.752,
        "Alkalinity": 218.365,
        "Hardness": 300.125,
        "Calcium": 337.178,
        "Ammonia": 0.286,
        "Nitrite": 4.355,
        "Phosphorus": 0.006,
        "H2S": 0.067,
        "Plankton": 6070
    }'
    ```

- **Response** (JSON):
    ```json
    {
        "quality_label": 2,
        "quality_name": "Good",
        "solution": "Monitor regularly."
    }
    ```
- **Lỗi**: Trả về `{"error": "message"}` với status code 400 hoặc 500 nếu có lỗi.

### 2. History API

Lấy lịch sử dữ liệu cảm biến và dự đoán.

- **Endpoint**: `GET /prediction/history`
- **Mô tả**: Trả về danh sách lịch sử các dự đoán chất lượng nước từ database.
- **Query Parameters**: (tùy chọn)
    - `limit`: Số lượng bản ghi trả về (mặc định 10)
    - `offset`: Bỏ qua số bản ghi đầu (mặc định 0)
- **Response** (JSON):
    ```json
    [
        {
            "_id": 4,
            "created_at": "2026-03-13T17:10:30.637827",
            "quality_label": 0,
            "quality_name": "Poor",
            "sensor_data": {
            "Alkalinity": 40.32,
            "Ammonia": 0.02,
            "BOD": 1.24,
            "CO2": 7.84,
            "Calcium": 52.1,
            "DO": 3.41,
            "H2S": 0.0197,
            "Hardness": 114.95,
            "Nitrite": 0.001,
            "Phosphorus": 0.99,
            "Plankton": 3092.0,
            "Temp": 21.79,
            "Turbidity": 78.26,
            "pH": 6.98
            },
            "solution": "Immediate action required."
        },
    ]
    ```
- **Lỗi**: Trả về `{"error": "message"}` với status code 500 nếu có lỗi database.

## Ghi chú

- Đảm bảo database được cấu hình đúng trong `be/app/config.py`.
- Model AI được train tự động từ file `WQD.xlsx` nếu có, hoặc từ dữ liệu trong database.
- Frontend kết nối tới backend qua API calls trong `fe/src/services/api.ts`.
- Predict.tsx và PredictTable.tsx tạo ra để test api bằng axios, làm xong thì xóa.
