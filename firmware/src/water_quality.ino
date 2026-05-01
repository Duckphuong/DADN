#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFiManager.h>
#include <NTPClient.h>
#include <WiFiUDP.h>
#include <SPIFFS.h>
#include <FS.h>
#include <vector>
#include <math.h>

// ============================================
// CONFIGURATION
// ============================================

// Backend API endpoint (loaded from SPIFFS config, with fallback default)
String backendURL = "http://192.168.135.169:5000/prediction/predict";  // Default fallback
const char* CONFIG_FILE = "/backend_config.txt";

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

// HTTP retry settings
const int HTTP_MAX_RETRIES = 3;
const unsigned long HTTP_RETRY_DELAY = 1000;

// Debug flag (set to 0 to disable Serial output)
#define DEBUG 1

#if DEBUG
#define DEBUG_PRINT(x) Serial.print(x)
#define DEBUG_PRINTLN(x) Serial.println(x)
#else

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
  // Real sensor
  float temperature;
  unsigned long timestamp;
  
  // Simulated parameters (cached)
  float turbidity;
  float dissolvedOxygen;
  float ph;
  float ammonia;
  float h2s;
  float bod;
  float co2;
  float alkalinity;
  float hardness;
  float calcium;
  float nitrite;
  float phosphorus;
  float plankton;
};
SensorReadings currentReadings;

// ============================================
// ECOSYSTEM SIMULATION (Replaces 13 simulated sensors)
// ============================================

// Simulate water quality ecosystem based on real temperature reading
// Models: nutrient cycling, plankton growth, DO balance, pH buffering, etc.
void simulateWaterQualityEcosystem() {
  float temp = currentReadings.temperature;
  
  // Temperature factor for biochemical reaction rates (Q10 ≈ 2.0)
  // At 25°C, factor = 1.0; reactions double per 10°C increase
  float tempRate = pow(2.0, (temp - 25.0) / 10.0);
  tempRate = max(0.1f, min(5.0f, tempRate));  // clamp to avoid extremes
  
  // ---------------------------------------------------------
  // 1. BASE NUTRIENTS & MINERALS (Input sources)
  // ---------------------------------------------------------
  // Phosphorus: from runoff/debris, slowly varying
  currentReadings.phosphorus = constrain(
    0.5 + random(-50, 50) / 100.0 + (temp - 20) * 0.008,
    0.0, 10.0
  );
  
  // Ammonia: from waste/decomposition, influenced by temperature
  currentReadings.ammonia = constrain(
    1.0 + random(-30, 30) / 100.0 + (temp - 20) * 0.015 * tempRate,
    0.0, 5.0
  );
  
  // Alkalinity: buffering capacity (relatively stable)
  currentReadings.alkalinity = constrain(
    120.0 + random(-10, 10) + (temp - 20) * 0.5,
    50.0, 300.0
  );
  
  // ---------------------------------------------------------
  // 2. NITROGEN CYCLE (Ammonia -> Nitrite)
  // ---------------------------------------------------------
  // Nitrification: NH3 -> NO2 (bacterial, temperature dependent)
  float nitrificationRate = 0.3 * tempRate;  // 30% conversion at 25°C
  currentReadings.nitrite = constrain(
    currentReadings.ammonia * nitrificationRate,
    0.0, 5.0
  );
  
  // ---------------------------------------------------------
  // 3. PRIMARY PRODUCTION (Plankton/Algae)
  // ---------------------------------------------------------
  // Algae growth depends on nutrients (P, N) and temperature
  float nutrientFactor = (currentReadings.phosphorus / 2.0) + (currentReadings.ammonia / 5.0);
  nutrientFactor = constrain(nutrientFactor, 0.0, 3.0);
  
  // Temperature optimum: algae prefer 20-30°C
  float tempGrowthFactor = 1.0 - fabs(temp - 25.0) / 30.0;
  tempGrowthFactor = max(0.1f, tempGrowthFactor);
  
  // Combined plankton biomass
  currentReadings.plankton = constrain(
    (nutrientFactor * 200.0 + (temp - 20.0) * 15.0) * tempGrowthFactor + random(-50, 50),
    10.0, 1000.0
  );
  
  // ---------------------------------------------------------
  // 4. TURBIDITY & BOD (Consequences of plankton)
  // ---------------------------------------------------------
  // Turbidity primarily from suspended algae + organic particles
  currentReadings.turbidity = constrain(
    2.0 + (currentReadings.plankton * 0.08) + random(-5, 5),
    0.0, 100.0
  );
  
  // BOD: organic matter decomposition (plankton death + waste)
  // Accelerates with temperature (faster metabolism)
  float decayRate = 0.03 * tempRate;
  currentReadings.bod = constrain(
    (currentReadings.plankton * 0.04 + currentReadings.ammonia * 2.0) * (1.0 + decayRate) + random(-2, 2),
    0.0, 50.0
  );
  
  // ---------------------------------------------------------
  // 5. DISSOLVED OXYGEN (DO) BALANCE
  // ---------------------------------------------------------
  float t = temp;
  float t2 = t * t;
  float t3 = t2 * t;
  
  // Saturation concentration (Benson-Krause approximate, mg/L)
  float do_sat = 14.652 - (0.41022 * t) + (0.007991 * t2) - (0.000077774 * t3);
  
  // DO consumption: BOD decomposition uses oxygen (respiration)
  float do_consumed = currentReadings.bod * 0.4;
  
  // DO production: photosynthesis by plankton (light-limited not modeled)
  float do_produced = currentReadings.plankton * 0.0015;
  
  currentReadings.dissolvedOxygen = constrain(
    do_sat - do_consumed + do_produced + random(-20, 20) / 10.0,
    0.0, 14.0
  );
  
  // ---------------------------------------------------------
  // 6. CO2 & pH (Inverse relationship with buffering)
  // ---------------------------------------------------------
  // CO2 sources: respiration + decomposition (proportional to BOD)
  // CO2 sinks: photosynthesis by plankton
  currentReadings.co2 = constrain(
    3.0 + (currentReadings.bod * 0.6) - (currentReadings.plankton * 0.001) + random(-2, 2),
    0.0, 100.0
  );
  
  // pH: Balance between alkaline buffer (alkalinity) and carbonic acid (CO2)
  // Alkalinity raises pH, CO2 lowers pH (forms H2CO3)
  float alkalinityEffect = (currentReadings.alkalinity - 100.0) * 0.004;
  float co2Effect = (currentReadings.co2 - 10.0) * 0.08;
  float basePh = 7.0 + alkalinityEffect - co2Effect;
  
  currentReadings.ph = constrain(
    basePh + random(-10, 10) / 10.0,
    4.0, 10.0
  );
  
  // ---------------------------------------------------------
  // 7. DERIVED MINERALS
  // ---------------------------------------------------------
  // Hardness correlates with alkalinity (carbonate hardness)
  currentReadings.hardness = constrain(
    currentReadings.alkalinity * 1.2 + random(-20, 20),
    50.0, 500.0
  );
  
  // Calcium is major component of hardness (~40%)
  currentReadings.calcium = constrain(
    currentReadings.hardness * 0.4 + random(-10, 10),
    20.0, 200.0
  );
  
  // H2S: hydrogen sulfide produced in anoxic conditions (very low DO)
  // Threshold: DO < 2 mg/L promotes anaerobic bacteria
  if (currentReadings.dissolvedOxygen < 2.0) {
    currentReadings.h2s = constrain(
      currentReadings.bod * 0.02 + random(-0.1, 0.1),
      0.0, 2.0
    );
  } else {
    currentReadings.h2s = constrain(
      currentReadings.bod * 0.005 + random(-0.05, 0.05),
      0.0, 1.0
    );
  }
}

// ============================================
// SENSOR READING
// ============================================

// Read physical sensors and simulate full water quality ecosystem
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
  
  // Read real temperature sensor (DS18B20)
  sensors.requestTemperatures();
  float temp = sensors.getTempCByIndex(0);
  
  if (temp == DEVICE_DISCONNECTED_C) {
    DEBUG_PRINTLN("Error: DS18B20 sensor disconnected!");
    currentReadings.temperature = 25.0;  // Default fallback
  } else {
    currentReadings.temperature = temp;
  }
  
  // Simulate ecosystem based on temperature
  simulateWaterQualityEcosystem();
}


// ============================================
// SENSOR ACCESS FUNCTIONS
// ============================================

// Real sensor
float getTemperature() {
  return currentReadings.temperature;
}

// Simulated sensors (return cached values from ecosystem simulation)
float getTurbidity() {
  return currentReadings.turbidity;
}

float getDissolvedOxygen() {
  return currentReadings.dissolvedOxygen;
}

float getPH() {
  return currentReadings.ph;
}

float getAmmonia() {
  return currentReadings.ammonia;
}

float getH2S() {
  return currentReadings.h2s;
}

float getBOD() {
  return currentReadings.bod;
}

float getCO2() {
  return currentReadings.co2;
}

float getAlkalinity() {
  return currentReadings.alkalinity;
}

float getHardness() {
  return currentReadings.hardness;
}

float getCalcium() {
  return currentReadings.calcium;
}

float getNitrite() {
  return currentReadings.nitrite;
}

float getPhosphorus() {
  return currentReadings.phosphorus;
}

float getPlankton() {
  return currentReadings.plankton;
}

// ============================================
// WIFI CONNECTION WITH EXPONENTIAL BACKOFF
// ============================================

bool connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;

  DEBUG_PRINTLN("Connecting to WiFi using WiFiManager...");
  
  // Initialize WiFiManager
  WiFiManager wifiManager;
  
  // Set timeout for config portal (3 minutes)
  wifiManager.setConfigPortalTimeout(180);
  
  // Try to connect - will start config portal if no saved credentials
  bool connected = wifiManager.autoConnect("WaterSensor_Config", "12345678");

  if (!connected) {
    DEBUG_PRINTLN("WiFi connection failed, restarting...");
    delay(3000);
    ESP.restart();
    return false;  // Won't reach here, but for completeness
  }

  DEBUG_PRINTLN("\nWiFi connected successfully!");
  DEBUG_PRINT("IP Address: ");
  DEBUG_PRINTLN(WiFi.localIP());

  // Start NTP sync if not already initialized
  if (!ntpInitialized) {
    ntpClient.begin();
    ntpInitialized = true;
  }
  ntpClient.update();

  return true;
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

// Load backend URL from config file
void loadBackendConfig() {
  if (SPIFFS.exists(CONFIG_FILE)) {
    File f = SPIFFS.open(CONFIG_FILE, "r");
    if (f) {
      String url = f.readStringUntil('\n');
      url.trim();
      if (url.length() > 0 && url.startsWith("http")) {
        backendURL = url;
        DEBUG_PRINT("Loaded backend URL from config: ");
        DEBUG_PRINTLN(backendURL);
      } else {
        DEBUG_PRINTLN("Invalid URL in config file, using default");
      }
      f.close();
    } else {
      DEBUG_PRINTLN("Failed to open config file");
    }
  } else {
    DEBUG_PRINTLN("Config file not found, using default URL");
  }
}

// Save backend URL to config file
bool saveBackendConfig(const String& url) {
  File f = SPIFFS.open(CONFIG_FILE, "w");
  if (f) {
    f.println(url);
    f.close();
    backendURL = url;
    DEBUG_PRINT("Saved backend URL: ");
    DEBUG_PRINTLN(url);
    return true;
  } else {
    DEBUG_PRINTLN("Failed to save config file");
    return false;
  }
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
        http.begin(backendURL);
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
       http.begin(backendURL);
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
  
  // Initialize SPIFFS for data queue
  initSPIFFS();
  
  // Load backend URL from config
  loadBackendConfig();
  
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
  sendSensorData();  // Send initial data immediately on startup
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
