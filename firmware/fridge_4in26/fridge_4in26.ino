// Fridge display: 4.26" mono e-ink (800x480) on XIAO ESP32-C3 + ePaper Driver Board V2.
// Wakes, fetches ready-to-draw JSON from the cloud endpoint, draws it, then deep-sleeps.
// If Wi-Fi or the server fails, it leaves the old image up and goes back to sleep.
//
// Build with Tools -> Partition Scheme -> "Huge APP (3MB No OTA/1MB SPIFFS)".
// Fonts and icons in assets.h come from tools/make_assets.py.

#include <WiFi.h>
#include <NetworkClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "TFT_eSPI.h"
#include "assets.h"
#include "secrets.h"

// ---- Settings ----
#define TEST_MODE 0          // 1 = refresh every minute. Set 0 for the fridge (server picks the schedule).
const int RETRY_MINUTES = 60;  // after a Wi-Fi or server failure

EPaper epaper;

// Layout, in screen pixels. Everything sits on a 110 px column grid starting at LEFT:
// the hourly forecast uses columns 0-6 and the AQI column starts on column 3.
const int LEFT = 40;
const int RIGHT = 760;
const int GRID = 110;
const int COL2 = LEFT + 3 * GRID;  // 370
const int HEADER_Y = 64;           // baselines
const int BIG_Y = 214;             // equal space above (to header) and below (to hours)
const int ROW1_Y = BIG_Y + 44;
const int ROW2_Y = BIG_Y + 82;
const int HOURS_Y = 336;           // top of the hourly icons
const int HOUR_T_Y = HOURS_Y + 76, HOUR_L_Y = HOURS_Y + 108;  // hourly temp and label baselines
const int BAR_W = RIGHT - COL2, BAR_H = 14, BAR_Y = ROW2_Y - 10 - BAR_H / 2;  // centered on the label's caps

void setup() {
  Serial.begin(115200);

  int sleepMin = RETRY_MINUTES;
  if (connectWiFi()) {
    JsonDocument doc;
    if (fetchData(doc)) {
      drawScreen(doc);
      sleepMin = doc["sleep_min"] | RETRY_MINUTES;
    }
  }
  goToSleep(TEST_MODE ? 1 : sleepMin);
}

void loop() {}  // never reached; deep sleep restarts setup()

// ---------- Wi-Fi + data ----------

bool connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for (int i = 0; i < 30 && WiFi.status() != WL_CONNECTED; i++) delay(500);  // up to 15 s
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi failed");
    return false;
  }
  Serial.println("Wi-Fi connected");
  return true;
}

bool fetchData(JsonDocument &doc) {
  NetworkClientSecure client;
  client.useBuiltinCACertBundle();  // verify the server's HTTPS certificate

  HTTPClient http;
  http.setTimeout(15000);
  if (!http.begin(client, ENDPOINT_URL)) return false;
  http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);

  int code = http.GET();
  if (code != 200) {
    Serial.printf("Server returned %d\n", code);
    http.end();
    return false;
  }
  DeserializationError err = deserializeJson(doc, http.getStream());
  http.end();
  if (err) {
    Serial.printf("Bad JSON: %s\n", err.c_str());
    return false;
  }
  serializeJson(doc, Serial);
  Serial.println();
  return true;
}

// ---------- Drawing helpers ----------

void text(const GFXfont &font, const String &s, int x, int baseline) {
  epaper.setFreeFont(&font);
  epaper.drawString(s, x, baseline);
}

int textW(const GFXfont &font, const String &s) {
  epaper.setFreeFont(&font);
  return epaper.textWidth(s);
}

const Icon *findIcon(const char *name) {
  for (int i = 0; i < ICON_COUNT; i++) {
    if (strcmp(ICONS[i].name, name) == 0) return &ICONS[i];
  }
  return nullptr;
}

void icon(const char *name, int x, int y) {
  const Icon *ic = findIcon(name);
  if (ic) epaper.drawBitmap(x, y, ic->bits, ic->size, ic->size, TFT_BLACK);
}

String fmtTemp(JsonVariantConst v) {
  return v.isNull() ? String("--") : String(v.as<int>()) + "°";
}

// Dot patterns stand in for grays, since the screen is black and white only.
bool shade(int level, int x, int y) {
  switch (level) {
    case 0: return false;                                         // white
    case 1: return (x % 4 == 0 && y % 4 == 0) || (x % 4 == 2 && y % 4 == 2);  // 12%
    case 2: return (x + y) % 2 == 0;                              // 50%
    case 3: return !(x % 2 == 1 && y % 2 == 1);                   // 75%
    case 4: return !(x % 4 == 1 && y % 4 == 1);                   // 94%
    default: return true;                                         // black
  }
}

void drawAqiBar(float pos) {
  const int x = COL2, y = BAR_Y;
  // 2 px frame
  epaper.fillRect(x, y, BAR_W, BAR_H, TFT_BLACK);
  const int ix = x + 2, iy = y + 2, iw = BAR_W - 4, ih = BAR_H - 4;
  epaper.fillRect(ix, iy, iw, ih, TFT_WHITE);

  for (int s = 0; s < 6; s++) {
    int x0 = ix + (s * iw) / 6;
    int x1 = ix + ((s + 1) * iw) / 6;
    for (int py = iy; py < iy + ih; py++) {
      for (int px = x0; px < x1; px++) {
        if (shade(s, px, py)) epaper.drawPixel(px, py, TFT_BLACK);
      }
    }
    if (s < 5) epaper.fillRect(x1 - 2, iy, 2, ih, TFT_BLACK);  // divider
  }

  // Marker: black dot with a white ring and a thin black outline.
  int cx = ix + (int)(pos * iw);
  int cy = y + BAR_H / 2;
  epaper.fillCircle(cx, cy, 13, TFT_BLACK);
  epaper.fillCircle(cx, cy, 11, TFT_WHITE);
  epaper.fillCircle(cx, cy, 7, TFT_BLACK);
}

// ---------- Screen ----------

void drawScreen(JsonDocument &d) {
  epaper.begin();
  epaper.fillScreen(TFT_WHITE);
  epaper.setTextColor(TFT_BLACK);
  epaper.setTextDatum(L_BASELINE);

  // Header: greeting on the left, date flush right.
  text(InterSemiBold40, d["greeting"] | "", LEFT, HEADER_Y);
  epaper.setTextDatum(R_BASELINE);
  text(InterSemiBold40, d["date"] | "", RIGHT, HEADER_Y);
  epaper.setTextDatum(L_BASELINE);

  // Middle row, centered between the header and the hourly row.
  // Left: temperature
  text(InterDisplayBold150, fmtTemp(d["temp"]), LEFT, BIG_Y);
  String hi = "H " + fmtTemp(d["hi"]);
  text(InterMedium26, hi, LEFT, ROW1_Y);
  text(InterMedium26, "L " + fmtTemp(d["lo"]), LEFT + textW(InterMedium26, hi) + 20, ROW1_Y);
  text(InterMedium26, d["precip_label"] | "", LEFT, ROW2_Y);

  // Right: air quality
  String aqi = d["aqi"].isNull() ? String("--") : String(d["aqi"].as<int>());
  text(InterDisplayBold150, aqi, COL2, BIG_Y);
  text(InterMedium26, d["aqi_label"] | "", COL2, ROW1_Y);
  if (!d["aqi"].isNull()) drawAqiBar(d["aqi_pos"] | 0.0f);

  // Bottom: next hours, one per grid column
  JsonArray hours = d["hours"];
  for (int i = 0; i < (int)hours.size() && i < 7; i++) {
    int x = LEFT + i * GRID;
    icon(hours[i]["icon"] | "cloud", x, HOURS_Y);
    text(InterBold34, fmtTemp(hours[i]["t"]), x, HOUR_T_Y);
    text(InterMedium26, hours[i]["label"] | "", x, HOUR_L_Y);
  }

  epaper.update();
  epaper.sleep();  // e-ink keeps the image with no power
}

// ---------- Sleep ----------

void goToSleep(int minutes) {
  if (minutes < 1) minutes = 1;
  Serial.printf("Sleeping %d min\n", minutes);
  Serial.flush();
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  esp_sleep_enable_timer_wakeup((uint64_t)minutes * 60ULL * 1000000ULL);
  esp_deep_sleep_start();
}
