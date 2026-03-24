# Water Quality Sensor Firmware

This firmware runs on an ESP32 microcontroller to read water quality sensors and send data to your Flask backend.

## Hardware Requirements

- ESP32 development board (e.g., ESP32 DevKit V1)
- **6 analog sensors for the following physical parameters:**
  - Temperature
  - Turbidity
  - Dissolved Oxygen (DO)
  - pH
  - Ammonia (NH3)
  - H2S

**Note:** The AI model expects 14 total parameters. The remaining 8 are **simulated in software** based on correlations with the 6 real sensors:
- BOD (Biochemical Oxygen Demand)
- CO2
- Alkalinity
- Hardness
- Calcium
- Nitrite
- Phosphorus
- Plankton

## Wiring

Connect the **6 physical sensors** to ADC1 pins on the ESP32:

| Sensor           | ESP32 Pin |
|------------------|-----------|
| Temperature      | GPIO35    |
| Turbidity        | GPIO36    |
| Dissolved Oxygen | GPIO37    |
| pH               | GPIO34    |
| Ammonia (NH3)    | GPIO33    |
| H2S              | GPIO32    |

**Important:**
- Use ADC1 pins (GPIO32-39) for analog readings on ESP32
- Ensure sensor output voltage is 0-3.3V (ESP32 ADC max is 3.3V). Use voltage dividers if needed.
- Power sensors appropriately (some may require 5V or excitation voltage).
- The 8 simulated parameters (BOD, CO2, Alkalinity, Hardness, Calcium, Nitrite, Phosphorus, Plankton) are **software-generated** and require no hardware connection.

## Configuration

Before uploading, edit the configuration section in `water_quality.ino`:

1. `WIFI_SSID` / `WIFI_PASSWORD` - Your WiFi network
2. `BACKEND_URL` - Your Flask backend URL (format: `http://IP_ADDRESS:5000/prediction/predict`)
3. (Optional) `SAMPLING_INTERVAL` - How often to send data (default: 60000ms = 1 minute)

## Sensor Calibration

### Physical Sensors (6)

You **must** calibrate these functions with your actual sensor datasheets:

- `getTemperature()` → Temperature (°C)
- `getTurbidity()` → Turbidity (NTU)
- `getDissolvedOxygen()` → DO (mg/L)
- `getPH()` → pH (0-14)
- `getAmmonia()` → Ammonia/NH3 (mg/L)
- `getH2S()` → H2S (mg/L)

Typical approaches:
- Linear conversion: `value = voltage * slope + intercept`
- Lookup tables
- Polynomial equations

Example from the code:
```cpp
float getTemperature() {
  sensors.requestTemperatures();
  return sensors.getTempCByIndex(0);
}
```

### Simulated Sensors (8)

These are **software-generated** based on correlations with real sensors. The current formulas are rough estimates. You can adjust `getBOD()`, `getCO2()`, `getAlkalinity()`, `getHardness()`, `getCalcium()`, `getNitrite()`, `getPhosphorus()`, and `getPlankton()` to match your domain knowledge or historical data patterns.

## Installation

### Prerequisites

1. Install Arduino IDE or PlatformIO (VS Code extension)
2. Add ESP32 board support:
   - In Arduino IDE: File → Preferences → Additional Boards Manager URLs → `https://dl.espressif.com/dl/package_esp32_index.json`
   - Then install "ESP32" via Boards Manager
3. Install required libraries (Arduino IDE):
   - ArduinoJson (by Benoit Blanchon)
   - HTTPClient (usually included with ESP32 core)

### Upload

1. Select your ESP32 board (e.g., "ESP32 Dev Module")
2. Select the correct COM port
3. Click Upload

## Testing

1. Open Serial Monitor at 115200 baud
2. Watch for WiFi connection and data being sent
3. Check your Flask backend to see if data arrives

## Backend Notes

- The firmware POSTs JSON to `/prediction/predict` with all 14 parameters
- Backend returns quality prediction and solution
- The firmware currently just prints the response to Serial (you could add an OLED display, LEDs, etc.)

## Troubleshooting

- **ADC readings unstable?** Try `readAverage()` function or add capacitors.
- **WiFi drops?** The code attempts reconnection in loop.
- **400 Bad Request from backend?** Check JSON formatting and parameter names match exactly.
- **No data in backend?** Check that the ESP32 and backend are on the same network, or that port 5000 is exposed.

## Customization Ideas

- Store readings locally if WiFi is down (use SPIFFS or SD card)
- Add MQTT instead of HTTP
- Include device_id in the JSON
- Display results on a screen
- Add buttons to trigger manual reads
- Power from battery with sleep modes
