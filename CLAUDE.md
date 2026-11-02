# E-ink Fridge Display

My first hardware project: a **battery-powered e-ink screen that hangs on the fridge with magnets** and shows:
1. **The average PurpleAir AQI** from sensors within 5 miles of home
2. **Today's high and low temperature**
3. **Whether rain or snow is in the forecast**

I've never built hardware before. This project is for learning how to plug parts together, so it uses **no soldering**. Explain hardware steps plainly and point out anything fragile or easy to get wrong.

## Status
- [x] Parts chosen and Seeed order placed on 2026-10-20 ($58.64, duties included); arrived 2026-10-30
- [ ] Buy the remaining parts (see below)
- [x] Get a PurpleAir API key and my latitude and longitude
- [x] Build the cloud data endpoint: Cloudflare Worker `fridge-display` at https://fridge-display.fridge-display-cloud.workers.dev (needs `Authorization: Bearer <DEVICE_TOKEN>`; secrets come from `cloud/.dev.vars` via `wrangler secret bulk`; KV `CACHE` caches results for 30 min)
- [ ] Write the firmware and connect the hardware
- [ ] Switch to battery power and mount it on the fridge

## Hardware
**Ordered from seeedstudio.com:**

| Item | SKU | Qty | Role |
|---|---|---|---|
| ePaper Driver Board for Seeed Studio XIAO (V2) | 114993558 | 2 | Adapter board: XIAO socket, 24-pin screen connector, JST battery plug with switch, built-in LiPo charging |
| XIAO ESP32-C3 (Pre-Soldered) | 102010633 | 2 | Wi-Fi microcontroller (the "brain"). Comes with a small U.FL Wi-Fi antenna; attach it. |
| 4.26" Monochrome ePaper, 800×480 | 114993631 | 1 | Main fridge screen |
| 2.9" Quadruple Color ePaper, 128×296 (black/white/red/yellow) | 104990855 | 1 | Experiment: AQI color-coded black, yellow or red. Refreshes in about 25 s, with flicker. |

The second XIAO and driver board are spares, and they also let both screens run at the same time.

**Still to buy elsewhere:**
- 2× 3.7V LiPo battery, **JST-PH 2.0** connector. Plan: **EEMB 963450 1800 mAh** (Amazon), whose listing diagram shows the correct polarity; still check each one on arrival. **Not EEMB B08214DJLJ (2000 mAh):** its polarity is reversed for this board. With the plug's ridged side facing you and the wires pointing down, red must be on the RIGHT.
- Adhesive neodymium magnets
- A USB-C cable that carries data
- A rigid backing for each screen (foamcore, cardboard, or a 3D-printed case)

**⚠️ Handle with care:**
- **Battery polarity:** before plugging the battery in, check that its red wire lines up with the **+** mark on the driver board. Plugging it in reversed can destroy the charging chip.
- **Screen ribbon cable:** never crease it, especially where it joins the glass. Open the connector latch gently.
- **Wi-Fi antenna:** press it straight down onto the U.FL connector and lift it straight up to remove it.

## Architecture
```
ESP32 wakes about every 60 min (skip overnight)
  → Wi-Fi → GET my cloud endpoint → small JSON
  → draw screen → display hibernate → deep sleep
Cloud endpoint (free tier)
  → PurpleAir: sensors in the area → average AQI
  → Open-Meteo: today's high, low and precipitation
```
- **The cloud does the math, and the device only displays.** This keeps the PurpleAir key off the device, keeps the firmware simple, and saves battery.
- **PurpleAir:** call `GET https://api.purpleair.com/v1/sensors` with:
  - `fields=pm2.5_cf_1,humidity,latitude,longitude` (the EPA correction is built on cf_1, not the 60-minute average)
  - `location_type=0` (outdoor sensors only)
  - `max_age=3600` (skip sensors silent for over an hour)
  - a bounding box (`nwlat`, `nwlng`, `selat`, `selng`)

  Then the endpoint:
  1. keeps sensors within 5 miles (haversine distance)
  2. applies the US EPA correction for PurpleAir
  3. averages the readings
  4. converts to AQI using the **2024 EPA PM2.5 cutoffs** (Good = 0–9.0 µg/m³)

  Cache for about 30 minutes; PurpleAir charges API points per request.
- **Open-Meteo** (free, no key): current temperature, hourly temperature/weather code/is_day, and daily max/min/precipitation/snowfall, in °F and inches, `timezone=auto`, `forecast_days=2`.
- **KV caches the raw upstream data for 30 min**; labels are built fresh on each request.
- **The JSON is ready to draw**, so the device only places it:
  `{greeting, date, temp, hi, lo, precip_icon, precip_label, aqi, aqi_label, aqi_pos, hours:[{t, icon, label}], sleep_min}`
- **`sleep_min`** wakes the device at 1 minute past each hour and skips 10 PM–6 AM.

## Firmware notes
- **Tools:** Arduino IDE 2, the ESP32 board package, and the **XIAO_ESP32C3** board. Seeed's wiki example wrongly says C6.
- **Libraries:**
  - **Seeed_GFX** (Seeed_Arduino_LCD), with a `driver.h` from the [Seeed_GFX configurator](https://seeed-studio.github.io/Seeed_GFX/) plus `#define USE_XIAO_EPAPER_DRIVER_BOARD` (BUSY on D2). Not `USE_XIAO_EPAPER_BREAKOUT_BOARD`, which puts BUSY on D5.
  - ArduinoJson
- **4.26" screen:** it uses the SSD1677 driver chip, with `BOARD_SCREEN_COMBO 506`, which is confirmed working.
- **Build** with Partition Scheme **Huge APP**, because the program is too big for the default.
- **Command line:** `arduino-cli compile --upload -p /dev/cu.usbmodem101 --fqbn esp32:esp32:XIAO_ESP32C3:PartitionScheme=huge_app firmware/fridge_4in26`. The CLI is bundled inside Arduino IDE.app.
- **Design:** Swiss style, all Geist, Phosphor icons, everything on a 110 px column grid. `assets.h` is generated by `firmware/tools/make_assets.py` (freetype-py) from the npm packages `geist` and `@phosphor-icons/web`.
- **`TEST_MODE 1`** in the sketch refreshes every minute; set it to 0 for the fridge.
- **2.9" 4-color screen:** get its combo ID from the configurator. The wiki's 504 is the 2.9" *mono* screen, so don't copy it.
- **Driver board pins:** RST D0, CS D1, BUSY D2, DC D3, SCK D8, MOSI D10.
- **Battery:**
  - Deep sleep between updates.
  - Call `epaper.sleep()` on the display after drawing.
  - If Wi-Fi fails, go back to sleep for 60 minutes; don't retry in a loop.
  - No battery %: the driver board has no circuit to measure the battery, which I checked in its schematic.

## Layout
```
cloud/                     # Cloudflare Worker; .dev.vars (gitignored) holds the secrets
firmware/fridge_4in26/     # main sketch; secrets.h (gitignored) holds Wi-Fi, URL, token
firmware/hello_4in26/      # Seeed HelloWorld screen test
firmware/tools/            # font/icon converter
```

## Build order (test each step before moving on)
1. Run the cloud endpoint locally and check its numbers against the PurpleAir map and a weather app. Then deploy it.
2. Plug in the XIAO on its own over USB and upload a blink or Wi-Fi-scan sketch.
3. With the power off, seat the XIAO in the driver board, connect the screen's ribbon cable, and run Seeed's example for that screen.
4. Upload my sketch and test it on USB with a 1-minute sleep.
5. Check the battery polarity, plug in the LiPo, set `TEST_MODE 0`, and check that it keeps updating for a few days.
6. Mount the screen on its backing and add the magnets.

## References
- Driver board wiki: https://wiki.seeedstudio.com/xiao_eink_expansion_board_v2/
- Seeed_GFX: https://github.com/Seeed-Studio/Seeed_GFX
- PurpleAir API: https://develop.purpleair.com
- Open-Meteo: https://open-meteo.com/en/docs
