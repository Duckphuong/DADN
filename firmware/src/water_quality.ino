#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Preferences.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <SPIFFS.h>
#include <FS.h>
#include <vector>

// ============================================
// CONFIGURATION MANAGEMENT
// ============================================

// Configuration keys for Preferences storage
#define PREF_NAMESPACE "water_quality"
#define PREF_WIFI_SSID "wifi_ssid"
#define PREF_WIFI_PASS "wifi_pass"
#define PREF_BACKEND_URL "backend_url"

// Default values (fallback if not configured)
const char* DEFAULT_WIFI_SSID = "your_wifi_ssid";
const char* DEFAULT_WIFI_PASSWORD = "your_wifi_password";
const char* DEFAULT_BACKEND_URL = "http://your-backend-ip:5000/prediction/predict";

// Runtime configuration (loaded from Preferences)
String config_wifi_ssid;
String config_wifi_password;
String config_backend_url;

// Load configuration from NVS (Preferences)
void loadConfig() {
  Preferences prefs;
  prefs.begin(PREF_NAMESPACE, true); // read-only
  
  config_wifi_ssid = prefs.getString(PREF_WIFI_SSID, DEFAULT_WIFI_SSID);
  config_wifi_password = prefs.getString(PREF_WIFI_PASS, DEFAULT_WIFI_PASSWORD);
  config_backend_url = prefs.getString(PREF_BACKEND_URL, DEFAULT_BACKEND_URL);
  
  prefs.end();
}

// Save configuration to NVS (for setup mode)
void saveConfig(const char* ssid, const char* pass, const char* url) {
  Preferences prefs;
  prefs.begin(PREF_NAMESPACE, false);
  
  prefs.putString(PREF_WIFI_SSID, ssid);
  prefs.putString(PREF_WIFI_PASS, pass);
  prefs.putString(PREF_BACKEND_URL, url);
  
  prefs.end();
}

// ============================================
// CONSTANTS
// ============================================

// Sensor Pin Assignments
const int PIN_TEMP = 4;            // Temperature - DS18B20 (1-Wire digital)

// OneWire setup for DS18B20
OneWire oneWire(PIN_TEMP);
DallasTemperature sensors(&oneWire);

// Sampling interval (milliseconds)
const unsigned long SAMPLING_INTERVAL = 60000;  // 1 minute

// WiFi reconnection backoff
const int WIFI_MAX_ATTEMPTS = 20;
const unsigned long WIFI_RETRY_DELAY = 500;

// HTTP retry settings
const int HTTP_MAX_RETRIES = 3;
const unsigned long HTTP_RETRY_DELAY = 1000;

// Debug flag (set to 0 to disable Serial output)
#define DEBUG 1

#if DEBUG
#define DEBUG_PRINT(x) Serial.print(x)
#define DEBUG_PRINTLN(x) Serial.println(x)
#else
#define DEBUG_PRINT(x)
#define DEBUG_PRINTLN(x)
#endif

// ============================================
// GLOBAL OBJECTS
// ============================================

// Global objects
WiFiUDP ntpUDP;
NTPClient ntpClient(ntpUDP, "pool.ntp.org", 25200);
bool ntpInitialized = false;

// SPIFFS handles for data persistence
File dataQueueFile;

// Device identification
String device_id;

struct SensorReadings {
  float temperature;
  unsigned long timestamp;        // Unix epoch timestamp
};
SensorReadings currentReadings;

// ============================================
// SENSOR READING
// ============================================

// Read the real temperature sensor and cache value
void readPhysicalSensors() {
  // Sync time if WiFi connected and NTP initialized
  if (WiFi.status() == WL_CONNECTED && ntpInitialized) {
    ntpClient.update();
    unsigned long epoch = ntpClient.getEpochTime();
    if (epoch > 1000000000) {  // sanity check (year > 2001)
      currentReadings.timestamp = epoch;
    } else {
      currentReadings.timestamp = millis() / 1000;  // fallback to uptime
    }
  } else {
    // Fallback to uptime if no WiFi or NTP not ready
    currentReadings.timestamp = millis() / 1000;
  }
  
  // Only read the real temperature sensor (DS18B20)
  sensors.requestTemperatures();
  float temp = sensors.getTempCByIndex(0);
  
  // Check for DS18B20 connection error
  if (temp == DEVICE_DISCONNECTED_C) {
    DEBUG_PRINTLN("Error: DS18B20 sensor disconnected!");
    currentReadings.temperature = 25.0;  // Default fallback value
  } else {
    currentReadings.temperature = temp;
  }
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

  DEBUG_PRINTLN("Connecting to WiFi...");
  WiFi.begin(config_wifi_ssid.c_str(), config_wifi_password.c_str());

  int attempt = 0;
  unsigned long lastPrint = millis();

  while (WiFi.status() != WL_CONNECTED && attempt < WIFI_MAX_ATTEMPTS) {
    if (millis() - lastPrint >= 500) {
      DEBUG_PRINT(".");
      lastPrint = millis();
    }
    delay(100);
    attempt++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    DEBUG_PRINTLN("\nConnected! IP address: ");
    DEBUG_PRINTLN(WiFi.localIP());
    // Start NTP sync if not already initialized
    if (!ntpInitialized) {
      ntpClient.begin();
      ntpInitialized = true;
    }
    ntpClient.update();
    return true;
  } else {
    DEBUG_PRINTLN("\nFailed to connect to WiFi");
    return false;
  }
}

// ============================================
// DATA PERSISTENCE (SPIFFS QUEUE)
// ============================================

// Initialize SPIFFS for data queue
bool initSPIFFS() {
  if (!SPIFFS.begin(true)) {
    DEBUG_PRINTLN("SPIFFS Mount Failed");
    return false;
  }
  DEBUG_PRINTLN("SPIFFS mounted");
  return true;
}

// Save failed payload to queue file for later retry
void enqueueFailedData(String& jsonString) {
  File f = SPIFFS.open("/dataqueue.txt", "a");
  if (f) {
    f.println(jsonString);
    f.close();
    DEBUG_PRINTLN("Data queued for retry");
  } else {
    DEBUG_PRINTLN("Failed to open queue file");
  }
}

// Retry sending queued data (called before sending new data)
void retryQueuedData() {
  if (!SPIFFS.exists("/dataqueue.txt")) return;
  
  File f = SPIFFS.open("/dataqueue.txt", "r");
  if (!f) return;
  
  // Read all queued lines
  std::vector<String> queuedPayloads;
  while (f.available()) {
    String line = f.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      queuedPayloads.push_back(line);
    }
  }
  f.close();
  
  // Remove queue file (we'll restore successful entries)
  SPIFFS.remove("/dataqueue.txt");
  
  // Retry each payload
  for (String& payload : queuedPayloads) {
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(config_backend_url.c_str());
      http.addHeader("Content-Type", "application/json");
      
      int httpCode = http.POST(payload);
      
      if (httpCode > 0 && httpCode < 300) {
        DEBUG_PRINT("Queued data delivered (code ");
        DEBUG_PRINT(httpCode);
        DEBUG_PRINTLN(")");
        http.end();
      } else {
        // Re-queue if still failing
        enqueueFailedData(payload);
        http.end();
        break; // Stop retrying remaining items if one fails (network likely still down)
      }
    } else {
      // Re-queue everything if WiFi not connected
      enqueueFailedData(payload);
    }
  }
}

// ============================================
// DATA COLLECTION & TRANSMISSION
// ============================================

void sendSensorData() {
  // Retry any previously queued data first
  retryQueuedData();
  
  // Read all physical sensors once and cache
  readPhysicalSensors();

  sensors.requestTemperatures();

  // Collect all sensor readings (simulated ones use cached values)
  StaticJsonDocument<512> doc;  // Reduced from 1024 (actual need ~300-400 bytes)
  doc["device_id"] = device_id;
  doc["timestamp"] = currentReadings.timestamp;
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

  DEBUG_PRINTLN("Sending data:");
  serializeJsonPretty(doc, Serial);
  DEBUG_PRINTLN();

  // Send to backend with retry logic
  if (WiFi.status() == WL_CONNECTED) {
    bool success = false;
    int attempt = 0;
    
    while (!success && attempt < HTTP_MAX_RETRIES) {
      HTTPClient http;
      http.begin(config_backend_url.c_str());
      http.addHeader("Content-Type", "application/json");

      int httpCode = http.POST(jsonString);

      // Check for successful HTTP response (200-299)
      if (httpCode > 0 && httpCode < 300) {
        String response = http.getString();
        DEBUG_PRINT("Response code: ");
        DEBUG_PRINTLN(httpCode);
        DEBUG_PRINT("Response: ");
        DEBUG_PRINTLN(response);
        success = true;
      } else if (httpCode > 0) {
        // HTTP error 
        DEBUG_PRINT("HTTP error: ");
        DEBUG_PRINTLN(httpCode);
        if (httpCode == 400) {
          DEBUG_PRINTLN("Bad Request - check JSON format and parameter names");
        } else if (httpCode == 500) {
          DEBUG_PRINTLN("Server error - check backend logs");
        }
        // Don't retry 4xx errors (client fault)
        if (httpCode >= 400 && httpCode < 500) {
          break;
        }
      } else {
        // Network error 
        DEBUG_PRINT("POST failed, error: ");
        DEBUG_PRINTLN(http.errorToString(httpCode).c_str());
      }

      http.end();
      
      if (!success) {
        attempt++;
        if (attempt < HTTP_MAX_RETRIES) {
          unsigned long backoff = HTTP_RETRY_DELAY * (1UL << (attempt - 1)); // 1s, 2s, 4s
          DEBUG_PRINT("Retrying in ");
          DEBUG_PRINT(backoff);
          DEBUG_PRINTLN(" ms...");
          delay(backoff);
        }
      }
    }
    
    if (!success) {
      DEBUG_PRINTLN("All retries failed, queuing data");
      enqueueFailedData(jsonString);
    }
  } else {
    DEBUG_PRINTLN("WiFi not connected, queuing data");
    enqueueFailedData(jsonString);
  }
}

// ============================================
// MAIN SETUP & LOOP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  DEBUG_PRINTLN("\n=== Water Quality Sensor Firmware ===");
  DEBUG_PRINTLN("Mode: One real temperature sensor (DS18B20) + simulated sensors");
  
  // Load configuration from Preferences
  loadConfig();
  
  // Initialize SPIFFS for data queue
  initSPIFFS();
  
  // Generate device ID from MAC address
  uint8_t mac[6];
  WiFi.macAddress(mac);
  char macStr[18];
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  device_id = String(macStr);
  
  DEBUG_PRINT("Device ID: ");
  DEBUG_PRINTLN(device_id);
  
  sensors.begin();
  
  // Connect WiFi (will also start NTP sync)
  connectWiFi();
}

void loop() {
  static unsigned long lastSend = 0;
  static bool wasConnected = false;
  
  if (millis() - lastSend >= SAMPLING_INTERVAL) {
    lastSend = millis();
    sendSensorData();
  }

  // Reconnect WiFi if disconnected (with rate-limited logging)
  bool isConnected = (WiFi.status() == WL_CONNECTED);
  
  if (!isConnected && wasConnected) {
    // Transition: connected -> disconnected
    DEBUG_PRINTLN("WiFi disconnected, trying to reconnect...");
    bool connected = connectWiFi();
    if (connected) {
      DEBUG_PRINTLN("WiFi reconnected");
    }
    delay(1000);  // wait before next check to avoid flooding
  } else if (!isConnected) {
    // Still disconnected, just retry without spamming
    bool connected = connectWiFi();
    if (connected) {
      DEBUG_PRINTLN("WiFi reconnected");
    }
    delay(5000);  // wait 5s between attempts when already disconnected
  }
  
  wasConnected = isConnected;
  
  delay(100);
}
