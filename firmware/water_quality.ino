#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ============================================
// CONFIGURATION - Edit these values
// ============================================
const char* WIFI_SSID = "your_wifi_ssid";
const char* WIFI_PASSWORD = "your_wifi_password";
const char* BACKEND_URL = "http://your-backend-ip:5000/prediction/predict";

// Sensor Pin Assignments - ONLY 6 PHYSICAL SENSORS
const int PIN_TEMP = 4;            // Temperature - DS18B20 (1-Wire digital)
const int PIN_TURBIDITY = 36;     // Turbidity (real, analog)
const int PIN_DO = 35;            // Dissolved Oxygen (real, analog)
const int PIN_PH = 34;            // pH (real, analog)
const int PIN_AMMONIA = 33;       // NH3 (real, analog)
const int PIN_H2S = 32;           // H2S (real, analog)

// OneWire setup for DS18B20
OneWire oneWire(PIN_TEMP);
DallasTemperature sensors(&oneWire);

// Sampling interval (milliseconds)
const unsigned long SAMPLING_INTERVAL = 60000;  // 1 minute
const int NUM_SAMPLES = 10;  // number of samples to average

// WiFi reconnection backoff
const int WIFI_MAX_ATTEMPTS = 20;
const unsigned long WIFI_RETRY_DELAY = 500;

// ============================================
// SENSOR DATA STRUCTURE (caching to avoid duplicate reads)
// ============================================

struct SensorReadings {
  float temperature;
  float turbidity;       // raw voltage
  float dissolvedOxygen; // raw voltage
  float ph;              // raw voltage
  float ammonia;         // raw voltage
  float h2s;             // raw voltage
};
SensorReadings currentReadings;

// ============================================
// LOW-LEVEL SENSOR READING
// ============================================

float readAnalog(int pin) {
  int raw = analogRead(pin);
  // Convert to voltage (ESP32 ADC is 12-bit: 0-4095)
  float voltage = raw * (3.3 / 4095.0);
  return voltage;
}

// Read all physical sensors once and cache values
void readPhysicalSensors() {
  sensors.requestTemperatures();
  currentReadings.temperature = sensors.getTempCByIndex(0);
  currentReadings.turbidity = readAverage(PIN_TURBIDITY, NUM_SAMPLES);
  currentReadings.dissolvedOxygen = readAverage(PIN_DO, NUM_SAMPLES);
  currentReadings.ph = readAverage(PIN_PH, NUM_SAMPLES);
  currentReadings.ammonia = readAverage(PIN_AMMONIA, NUM_SAMPLES);
  currentReadings.h2s = readAverage(PIN_H2S, NUM_SAMPLES);
}

// Optional: average multiple readings for stability
float readAverage(int pin, int samples = NUM_SAMPLES) {
  float sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += readAnalog(pin);
    delay(10);
  }
  return sum / samples;
}

// ============================================
// REAL SENSOR FUNCTIONS (6 physical sensors)
// ============================================

float getTemperature() {
  return currentReadings.temperature;
}

float getTurbidity() {
  // TODO: Calibrate based on your turbidity sensor (e.g., convert voltage to NTU)
  return currentReadings.turbidity * 1000.0;
}

float getDissolvedOxygen() {
  // TODO: Calibrate based on your DO sensor
  return currentReadings.dissolvedOxygen * 10.0;
}

float getPH() {
  // TODO: Calibrate pH sensor (typically 0-3V → pH 0-14)
  return currentReadings.ph * (14.0 / 3.3);
}

float getAmmonia() {
  // TODO: Calibrate ammonia sensor
  return currentReadings.ammonia * 10.0;
}

float getH2S() {
  // TODO: Calibrate H2S sensor
  return currentReadings.h2s * 10.0;
}

// ============================================
// SIMULATED SENSOR FUNCTIONS (8 software-generated values)
// ============================================

// These sensors are not physically connected.
// They are estimated based on correlations with real sensors.
// IMPORTANT: Use cached voltage values to avoid duplicate ADC reads.

float getBOD() {
  // BOD correlates with DO and temperature
  float temp = currentReadings.temperature;
  float do_val = currentReadings.dissolvedOxygen * 10.0;  // to mg/L
  float bod = 2.0 + (10.0 - do_val) * 0.5 + (temp - 20) * 0.1;
  return constrain(bod, 0.0, 50.0);
}

float getCO2() {
  // CO2 estimated from pH and temperature
  float ph = currentReadings.ph * (14.0 / 3.3);  // to pH
  float co2 = 10.0 * (7.0 - ph) + 5.0;
  return constrain(co2, 0.0, 100.0);
}

float getAlkalinity() {
  float ph = currentReadings.ph * (14.0 / 3.3);
  float alkalinity = 100.0 + (ph - 7.0) * 20.0;
  return constrain(alkalinity, 20.0, 500.0);
}

float getHardness() {
  float ph = currentReadings.ph * (14.0 / 3.3);
  float turbidity = currentReadings.turbidity * 1000.0;  // to NTU
  float hardness = 150.0 + ph * 10.0 + turbidity * 5.0;
  return constrain(hardness, 50.0, 500.0);
}

float getCalcium() {
  float hardness = getHardness();
  return hardness * 0.6;
}

float getNitrite() {
  float ammonia = currentReadings.ammonia * 10.0;  // to mg/L
  float nitrite = ammonia * 0.2;
  return constrain(nitrite, 0.0, 5.0);
}

float getPhosphorus() {
  float turbidity = currentReadings.turbidity * 1000.0;
  float phosphorus = turbidity * 0.5;
  return constrain(phosphorus, 0.0, 10.0);
}

float getPlankton() {
  float turbidity = currentReadings.turbidity * 1000.0;
  float do_val = currentReadings.dissolvedOxygen * 10.0;
  float plankton = turbidity * 2.0 + (8.0 - do_val) * 0.5;
  return constrain(plankton, 0.0, 1000.0);
}

// ============================================
// WIFI CONNECTION WITH EXPONENTIAL BACKOFF
// ============================================

bool connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");

  int attempt = 0;
  unsigned long lastPrint = millis();

  while (WiFi.status() != WL_CONNECTED && attempt < WIFI_MAX_ATTEMPTS) {
    // Print dot every 500ms to show progress
    if (millis() - lastPrint >= 500) {
      Serial.print(".");
      lastPrint = millis();
    }
    delay(100);  // small poll interval to avoid blocking too long
    attempt++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected! IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println("\nFailed to connect to WiFi");
    return false;
  }
}

// ============================================
// DATA COLLECTION & TRANSMISSION
// ============================================

void sendSensorData() {
  // Read all physical sensors once and cache
  readPhysicalSensors();

  // Small delay to let DS18B20 settle if needed
  delay(50);

  // Collect all sensor readings (simulated ones use cached values)
  StaticJsonDocument<1024> doc;
  doc["Temp"] = getTemperature();
  doc["Turbidity"] = getTurbidity();
  doc["DO"] = getDissolvedOxygen();
  doc["BOD"] = getBOD();
  doc["CO2"] = getCO2();
  doc["pH"] = getPH();
  doc["Alkalinity"] = getAlkalinity();
  doc["Hardness"] = getHardness();
  doc["Calcium"] = getCalcium();
  doc["Ammonia"] = getAmmonia();
  doc["Nitrite"] = getNitrite();
  doc["Phosphorus"] = getPhosphorus();
  doc["H2S"] = getH2S();
  doc["Plankton"] = getPlankton();

  String jsonString;
  serializeJson(doc, jsonString);

  Serial.println("Sending data:");
  Serial.println(jsonString);

  // Send to backend
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(BACKEND_URL);
    http.addHeader("Content-Type", "application/json");

    int httpCode = http.POST(jsonString);

    // Check for successful HTTP response (200-299)
    if (httpCode > 0 && httpCode < 300) {
      String response = http.getString();
      Serial.print("Response code: ");
      Serial.println(httpCode);
      Serial.print("Response: ");
      Serial.println(response);
    } else if (httpCode > 0) {
      // HTTP error (4xx, 5xx)
      Serial.print("HTTP error: ");
      Serial.println(httpCode);
      if (httpCode == 400) {
        Serial.println("Bad Request - check JSON format and parameter names");
      } else if (httpCode == 500) {
        Serial.println("Server error - check backend logs");
      }
    } else {
      // Network error (connection failed, timeout, etc.)
      Serial.print("POST failed, error: ");
      Serial.println(http.errorToString(httpCode).c_str());
    }

    http.end();
  } else {
    Serial.println("WiFi not connected, skipping send");
  }
}

// ============================================
// MAIN SETUP & LOOP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Water Quality Sensor Firmware ===");
  sensors.begin();

  // Initialize analog pins as inputs
  pinMode(PIN_TURBIDITY, INPUT);
  pinMode(PIN_DO, INPUT);
  pinMode(PIN_PH, INPUT);
  pinMode(PIN_AMMONIA, INPUT);
  pinMode(PIN_H2S, INPUT);

  connectWiFi();
}

void loop() {
  static unsigned long lastSend = 0;
  if (millis() - lastSend >= SAMPLING_INTERVAL) {
    lastSend = millis();
    sendSensorData();
  }

  // Reconnect WiFi if disconnected (with brief delay to avoid busy loop)
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, trying to reconnect...");
    bool connected = connectWiFi();
    if (connected) {
      Serial.println("WiFi reconnected");
    }
    delay(1000);  // wait before next check to avoid flooding
  }

  delay(100);  // reduce from 1000ms to be more responsive to timing
}
