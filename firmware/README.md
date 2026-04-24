# Firmware Cảm biến Chất lượng Nước

Firmware này chạy trên vi điều khiển ESP32 để đọc dữ liệu từ các cảm biến chất lượng nước và gửi dữ liệu đến backend Flask của bạn.

## Yêu cầu Phần cứng

- ESP32 development board (ví dụ: ESP32 DevKit V1)
- **6 cảm biến analog/digital cho các thông số vật lý sau:**
  - Nhiệt độ (DS18B20 - 1-Wire digital)
  - Độ đục (Turbidity) (analog)
  - Oxy hòa tan (DO) (analog)
  - pH (analog)
  - Amoniac (NH3) (analog)
  - H2S (analog)

**Lưu ý:** Mô hình AI yêu cầu tổng cộng 14 tham số. 8 tham số còn lại được **mô phỏng bằng phần mềm** dựa trên mối tương quan với 6 cảm biến thực:
- BOD (Biochemical Oxygen Demand - Nhu cầu oxy hóa học)
- CO2
- Alkalinity (Tính kiềm)
- Hardness (Độ cứng)
- Calcium
- Nitrite
- Phosphorus
- Plankton (Vi sinh vật nổi)

## Kết nối Dây (Wiring)

### Cảm biến Nhiệt độ (DS18B20) - Digital (1-Wire)
Kết nối cảm biến nhiệt độ DS18B20 vào **GPIO 4** (Pin D4 trên nhiều board ESP32):
- VCC → 3.3V hoặc 5V (kiểm tra phiên bản DS18B20 của bạn)
- GND → GND
- DATA → GPIO 4 (với điện trở kéo lên 4.7kΩ lên VCC)

### Cảm biến Analog (5 cảm biến)
Kết nối **5 cảm biến analog** (Turbidity, DO, pH, Ammonia, H2S) vào các chân ADC1 trên ESP32:

| Cảm biến           | Chân ESP32 | Kênh ADC |
|--------------------|------------|----------|
| Độ đục (Turbidity) | GPIO 36    | ADC1 CH0 |
| Oxy hòa tan (DO)   | GPIO 35    | ADC1 CH1 |
| pH                 | GPIO 34    | ADC1 CH6 |
| Amoniac (NH3)      | GPIO 33    | ADC1 CH7 |
| H2S                | GPIO 32    | ADC1 CH4 |

**Quan trọng:**
- Sử dụng chân ADC1 (GPIO32-39) để đọc analog trên ESP32
- Đảm bảo điện áp đầu ra cảm biến là 0-3.3V (ADC ESP32 tối đa 3.3V). Sử dụng chia điện áp nếu cần.
- Cấp nguồn cho cảm biến phù hợp (một số có yêu cầu 5V hoặc điện áp kích hoạt).
- 8 tham số được mô phỏng (BOD, CO2, Alkalinity, Hardness, Calcium, Nitrite, Phosphorus, Plankton) được **tạo ra bằng phần mềm** và không cần kết nối phần cứng.

## Cấu hình

### WiFi Configuration (Auto via WiFiManager)

Firmware sử dụng **WiFiManager** để tự động kết nối WiFi qua captive portal:

1. Khi khởi động, ESP32 sẽ tìm kiếm WiFi đã lưu
2. Nếu không có WiFi đã lưu, ESP32 tạo Access Point tên **"WaterSensor_Config"** với mật khẩu **"12345678"**
3. Kết nối vào AP này từ điện thoại/laptop
4. Trình duyệt sẽ tự động mở trang cấu hình (hoặc truy cập 192.168.4.1)
5. Chọn mạng WiFi của bạn và nhập mật khẩu
6. Nhấn "Save" - ESP32 sẽ kết nối và lưu cấu hình

**Lưu ý:** 
- Config portal tự động tắt sau 3 phút nếu không có thiết bị kết nối
- Thông tin WiFi được lưu trong ESP32, không cần cấu hình lại khi upload Firmware mới
- Nếu muốn xóa cấu hình cũ, giữ nút RESET/GPIO0 khi khởi động (hoặc dùng `wifiManager.resetSettings()` trong code)

### Backend URL

Hiện tại `BACKEND_URL` được hardcode trong firmware:
```cpp
const char* BACKEND_URL = "http://your-backend-ip:5000/prediction/predict";
```

Thay đổi IP address trong code trước khi upload, hoặc thêm Serial command interface để cấu hình từ xa (tính năng tương lai).

## Hiệu chuẩn Cảm biến

### Cảm biến Vật lý (6)

Bạn **phải** hiệu chuẩn các hàm này với bảng dữ liệu cảm biến thực tế của mình:

- `getTemperature()` → Nhiệt độ (°C) - DS18B20 cung cấp Celsius đã hiệu chuẩn
- `getTurbidity()` → Độ đục (NTU) - Chuyển đổi điện áp sang NTU bằng: `voltage * 1000.0`
- `getDissolvedOxygen()` → DO (mg/L) - Chuyển đổi điện áp sang mg/L bằng: `voltage * 10.0`
- `getPH()` → pH (0-14) - Chuyển đổi điện áp sang pH bằng: `voltage * (14.0 / 3.3)`
- `getAmmonia()` → Amoniac/NH3 (mg/L) - Chuyển đổi điện áp sang mg/L bằng: `voltage * 10.0`
- `getH2S()` → H2S (mg/L) - Chuyển đổi điện áp sang mg/L bằng: `voltage * 10.0`

Các phương pháp phổ biến:
- Chuyển đổi tuyến tính: `value = voltage * slope + intercept`
- Bảng tra (lookup tables)
- Phương trình đa thức (polynomial equations)

Ví dụ từ code:
```cpp
float getTemperature() {
  sensors.requestTemperatures();
  return sensors.getTempCByIndex(0);
}
```

### Cảm biến Mô phỏng (8)

Đây là các giá trị **được tạo ra bằng phần mềm** dựa trên mối tương quan với cảm biến thực. Các công thức hiện tại là ước tính thô. Bạn có thể điều chỉnh `getBOD()`, `getCO2()`, `getAlkalinity()`, `getHardness()`, `getCalcium()`, `getNitrite()`, `getPhosphorus()`, và `getPlankton()` để khớp với kiến thức lĩnh vực hoặc mẫu dữ liệu lịch sử của bạn.

## Cài đặt với PlatformIO (Khuyến nghị)

### Yêu cầu tiên quyết

1. **PlatformIO** - Cài đặt qua VS Code (extension PlatformIO IDE) hoặc CLI:
   ```bash
   pip install platformio
   ```

2. **ESP32 Board Support** - PlatformIO tự động tải về khi build lần đầu

### File `platformio.ini`

Project sử dụng PlatformIO với file cấu hình `platformio.ini`:

```ini
[env:esp32s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino

lib_deps =
    bblanchon/ArduinoJson
    paulstoffregen/OneWire
    milesburton/DallasTemperature
    arduino-libraries/NTPClient
    tzapu/WiFiManager
```

**Các mục cấu hình:**
- `platform = espressif32` - Nền tảng ESP32
- `board = esp32-s3-devkitc-1` - Board ESP32-S3 DevKit (có thể thay đổi nếu dùng board khác)
- `framework = arduino` - Sử dụng Arduino framework
- `lib_deps` - Các thư viện dependencies:
  - `bblanchon/ArduinoJson` - Thư viện JSON serialization
  - `paulstoffregen/OneWire` - Bus 1-Wire cho DS18B20
  - `milesburton/DallasTemperature` - Thư viện cảm biến nhiệt độ
  - `arduino-libraries/NTPClient` - Đồng bộ thời gian qua NTP
  - `tzapu/WiFiManager` - Quản lý WiFi với captive portal

### Upload Firmware với PlatformIO

```bash
cd /home/node/project1/firmware
pio run -t upload
```

**Các lệnh PlatformIO**
```bash
pio run                    # Build firmware
pio run -t upload          # Build và upload
pio run -t monitor         # Upload và mở Serial Monitor
pio device list            # Liệt kê các board ESP32 đã kết nối
pio run -t clean           # Xóa build artifacts
```

**Khi upload:**
1. Kết nối ESP32 qua USB
2. Chạy lệnh upload (`pio run -t upload`)
3. PlatformIO sẽ tự động compile dependencies và upload firmware


## Cài đặt với Arduino IDE (Alternative)

1. Cài đặt Arduino IDE 
2. Add ESP32 board support:
   - Trong Arduino IDE: File → Preferences → Additional Boards Manager URLs → `https://dl.espressif.com/dl/package_esp32_index.json`
   - Sau đó cài "ESP32" qua Boards Manager
3. Cài đặt các thư viện cần thiết (Arduino IDE Library Manager):
   - **ArduinoJson** (by Benoit Blanchon) - để serialize JSON
   - **OneWire** - cho cảm biến DS18B20
   - **DallasTemperature** - cho cảm biến DS18B20
   - HTTPClient (thường có sẵn với ESP32 core)

### Cài đặt Thư viện (Arduino IDE)
- Tìm kiếm "ArduinoJson" và cài đặt
- Tìm kiếm "OneWire" và cài đặt
- Tìm kiếm "DallasTemperature" và cài đặt

### Upload với Arduino IDE

1. Chọn board ESP32 (ví dụ: "ESP32 Dev Module")
2. Chọn cổng COM phù hợp
3. Nhấn Upload

## Kiểm tra (Testing)

1. Mở Serial Monitor ở 115200 baud
2. Quan sát kết nối WiFi và dữ liệu được gửi mỗi 60 giây
3. Bạn sẽ thấy đầu ra JSON như:
```json
{"Temp":24.5,"Turbidity":3.2,"DO":7.8,"BOD":1.24,"CO2":7.84,"pH":6.98,"Alkalinity":40.32,"Hardness":114.95,"Calcium":52.1,"Ammonia":0.02,"Nitrite":0.001,"Phosphorus":0.99,"H2S":0.0197,"Plankton":3092.0}
```
4. Kiểm tra backend Flask của bạn để xem dữ liệu có đến và predictions được trả về

## Ghi chú Backend

- Firmware POST JSON đến `/prediction/predict` với tất cả 14 tham số
- Backend trả về dự đoán chất lượng và giải pháp: `{"quality_label":2,"quality_name":"Good","solution":"Monitor regularly."}`
- Firmware in phản hồi ra Serial (bạn có thể thêm màn hình OLED, LED, v.v. để có phản hồi trực quan)
- Backend tự động lưu tất cả predictions vào cơ sở dữ liệu SQLite

## Định dạng API Endpoint

**Endpoint:** `POST http://your-backend-ip:5000/prediction/predict`

**Request Body (JSON):**
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

**Response (JSON):**
```json
{
    "quality_label": 2,
    "quality_name": "Good",
    "solution": "Monitor regularly."
}
```

## Khắc phục Sự cố (Troubleshooting)

- **Đọc ADC không ổn định?** Thử tăng `NUM_SAMPLES` hoặc thêm điện dung vào đầu ra cảm biến.
- **Không phát hiện cảm biến nhiệt độ?** Kiểm tra kết nối DS18B20 (chân dữ liệu vào GPIO 4) và điện trở kéo lên 4.7kΩ.
- **WiFi bị ngắt?** Code cố gắng kết nối lại với exponential backoff.
- **400 Bad Request từ backend?** Kiểm tra định dạng JSON và tên tham số khớp chính xác.
- **Không có dữ liệu trong backend?** Xác minh ESP32 và backend cùng mạng, và port 5000 có thể truy cập được. Kiểm tra cài đặt firewall.
- **Lỗi PlatformIO?** Đảm bảo chạy lệnh từ thư mục `firmware/`
- **Lỗi thư viện?** Đảm bảo tất cả thư viện cần thiết (ArduinoJson, OneWire, DallasTemperature) đã được cài đặt trong `platformio.ini`.

## Ý tưởng Tùy chỉnh

- Lưu trữ readings cục bộ nếu WiFi ngừng hoạt động (dùng SPIFFS hoặc thẻ SD)
- Thêm MQTT thay vì HTTP cho tích hợp IoT
- Bao gồm device_id trong JSON để theo dõi nhiều thiết bị
- Hiển thị kết quả trên màn hình OLED (SSD1306)
- Thêm LED hoặc buzzer cho chỉ báo trạng thái/cảnh báo
- Thêm nút để kích hoạt đọc thủ công hoặc cấu hình
- Cấp nguồn từ pin với chế độ deep sleep để tiết kiệm năng lượng
- Thực hiện URL backend có thể cấu hình qua WiFi captive portal hoặc lệnh serial
