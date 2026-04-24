#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ============================================
// CONFIGURATION - UPDATE THESE BEFORE UPLOADING
// ============================================
const char* WIFI_SSID = "your_wifi_ssid";
const char* WIFI_PASSWORD = "your_wifi_password";
const char* BACKEND_URL = "http://your-backend-ip:5000/prediction/predict";

// Sensor Pin Assignments 
const int PIN_TEMP = 4;            // Temperature - DS18B20 (1-Wire digital, REAL SENSOR)

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
// SENSOR DATA STRUCTURE 
// ============================================

struct SensorReadings {
  float temperature;
};
SensorReadings currentReadings;

// ============================================
// SENSOR READING
// ============================================

// Read the real temperature sensor and cache value
void readPhysicalSensors() {
  // Only read the real temperature sensor (DS18B20)
  sensors.requestTemperatures();
  currentReadings.temperature = sensors.getTempCByIndex(0);
}


// ============================================
// REAL SENSOR FUNCTION
// ============================================

float getTemperature() {
  return currentReadings.temperature;
}

// ============================================
// SIMULATED SENSOR FUNCTIONS (13 software-generated values)
// ============================================

// All sensors except temperature are simulated.
// They are estimated based on correlations with the real temperature sensor.

float getTurbidity() {
  // Turbidity varies with temperature
  float temp = currentReadings.temperature;
  float turbidity = 5.0 + (temp - 20) * 0.3;
  return constrain(turbidity, 0.0, 100.0);
}

float getDissolvedOxygen() {
  // DO inversely correlates with temperature
  float temp = currentReadings.temperature;
  float do_val = 10.0 - (temp - 20) * 0.15;
  return constrain(do_val, 0.0, 14.0);
}

float getPH() {
  // pH varies slightly with temperature
  float temp = currentReadings.temperature;
  float ph = 7.0 + (temp - 20) * 0.02;
  return constrain(ph, 4.0, 10.0);
}

float getAmmonia() {
  // Ammonia increases with temperature
  float temp = currentReadings.temperature;
  float ammonia = 0.2 + (temp - 20) * 0.02;
  return constrain(ammonia, 0.0, 5.0);
}

float getH2S() {
  // H2S varies with temperature
  float temp = currentReadings.temperature;
  float h2s = 0.1 + (temp - 20) * 0.01;
  return constrain(h2s, 0.0, 1.0);
}

float getBOD() {
  // BOD correlates with temperature
  float temp = currentReadings.temperature;
  float bod = 2.0 + (temp - 20) * 0.1;
  return constrain(bod, 0.0, 50.0);
}

float getCO2() {
  // CO2 estimated from temperature
  float temp = currentReadings.temperature;
  float co2 = 10.0 + (temp - 20) * 0.5;
  return constrain(co2, 0.0, 100.0);
}

float getAlkalinity() {
  float temp = currentReadings.temperature;
  float alkalinity = 100.0 + (temp - 20) * 2.0;
  return constrain(alkalinity, 20.0, 500.0);
}

float getHardness() {
  float temp = currentReadings.temperature;
  float hardness = 150.0 + (temp - 20) * 3.0;
  return constrain(hardness, 50.0, 500.0);
}

float getCalcium() {
  // Calcium estimated from temperature
  float temp = currentReadings.temperature;
  float calcium = 60.0 + (temp - 20) * 1.0;
  return constrain(calcium, 20.0, 200.0);
}

float getNitrite() {
  // Nitrite estimated from temperature
  float temp = currentReadings.temperature;
  float nitrite = 0.05 + (temp - 20) * 0.01;
  return constrain(nitrite, 0.0, 5.0);
}

float getPhosphorus() {
  // Phosphorus estimated from temperature
  float temp = currentReadings.temperature;
  float phosphorus = 0.5 + (temp - 20) * 0.02;
  return constrain(phosphorus, 0.0, 10.0);
}

float getPlankton() {
  // Plankton estimated from temperature
  float temp = currentReadings.temperature;
  float plankton = 100.0 + (temp - 20) * 5.0;
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
  JsonDocument doc;
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
      // HTTP error 
      Serial.print("HTTP error: ");
      Serial.println(httpCode);
      if (httpCode == 400) {
        Serial.println("Bad Request - check JSON format and parameter names");
      } else if (httpCode == 500) {
        Serial.println("Server error - check backend logs");
      }
    } else {
      // Network error 
      Serial.print("POST failed, error: ");
      Serial.println(http.errorToString(httpCode).c_str());
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

// ============================================
// MAIN SETUP & LOOP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Water Quality Sensor Firmware ===");
  Serial.println("Mode: One real temperature sensor (DS18B20) + simulated sensors");
  sensors.begin();

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
