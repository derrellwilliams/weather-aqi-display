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
- [x] Build the cloud data endpoint: Cloudflare Worker with a private name in gitignored `cloud/.worker-name` (URL lives in `firmware/fridge_4in26/secrets.h`; needs `Authorization: Bearer <DEVICE_TOKEN>`; deploy with `npm run deploy`, upload `cloud/.dev.vars` secrets with `npm run secrets`; KV `CACHE` caches results for 30 min)
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
- **Screen ribbon cable:** never crease it, especially where it joins the glass. Open the connector latch gently. It can work loose when you plug and unplug things, and then the screen just stops updating with no error. Once it's mounted, tape the ribbon to the backing so it can't pull on the connector.
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
- **`sleep_min`** wakes the device at 1 minute past each hour and sleeps after the 11:01 PM update until 4:01 AM.

## Firmware notes
- **Tools:** Arduino IDE 2, the ESP32 board package, and the **XIAO_ESP32C3** board. Seeed's wiki example wrongly says C6.
- **Libraries:**
  - **Seeed_GFX** (Seeed_Arduino_LCD), with a `driver.h` from the [Seeed_GFX configurator](https://seeed-studio.github.io/Seeed_GFX/) plus `#define USE_XIAO_EPAPER_DRIVER_BOARD` (BUSY on D2). Not `USE_XIAO_EPAPER_BREAKOUT_BOARD`, which puts BUSY on D5.
  - ArduinoJson
- **4.26" screen:** it uses the SSD1677 driver chip, with `BOARD_SCREEN_COMBO 506`, which is confirmed working.
- **Build** with Partition Scheme **Huge APP**, because the program is too big for the default.
- **Design:** Swiss style, all Inter (Inter Display Bold for the big numbers), Phosphor icons, everything on a 110 px column grid. `assets.h` is generated by `firmware/tools/make_assets.py` (freetype-py) from the Inter release zip (`extras/ttf`, github.com/rsms/inter) and the npm package `@phosphor-icons/web`. Preview a layout change with `render_preview.py` before flashing.
- **`TEST_MODE 1`** in the sketch refreshes every minute; set it to 0 for the fridge.
- **2.9" 4-color screen:** get its combo ID from the configurator. The wiki's 504 is the 2.9" *mono* screen, so don't copy it.
- **Driver board pins:** RST D0, CS D1, BUSY D2, DC D3, SCK D8, MOSI D10.
- **Battery:**
  - Deep sleep between updates.
  - Call `epaper.sleep()` on the display after drawing.
  - If Wi-Fi fails, go back to sleep for 60 minutes; don't retry in a loop.
  - No battery %: the driver board has no circuit to measure the battery, which I checked in its schematic.

## Build, flash and read the log
The CLI is bundled inside Arduino IDE.app at `Contents/Resources/app/lib/backend/resources/arduino-cli`.
1. **Compile** (runs in the sandbox): `arduino-cli compile --libraries ~/.arduino/libraries --build-path firmware/build/<sketch> --fqbn esp32:esp32:XIAO_ESP32C3:PartitionScheme=huge_app firmware/<sketch>`
2. **Upload:** `~/.local/bin/fridge-flash [sketch]` (the default sketch is `fridge_4in26`). It finds the port and waits up to 90 s for the board to wake.
3. **Read the log:** `~/.local/bin/fridge-serial [seconds]` (default 90). A good cycle prints `Wi-Fi connected`, then the JSON, then `Sleeping N min`. Failures print `Wi-Fi failed`, `Server returned <code>` or `Bad JSON`. To see a whole cycle from the start, start listening, then tap R.

**Sandbox setup (Claude):**
- **Libraries live in `~/.arduino/libraries`** (ArduinoJson, Seeed_GFX), not `~/Documents/Arduino`, which the sandbox can't read. `--build-path` keeps builds out of `~/Library/Caches`, which the sandbox also blocks. `firmware/build/` is gitignored.
- **Serial access can't run in the sandbox.** macOS blocks setting the serial port's speed (`termios`, `Operation not permitted`) even when the port file is allowed, and no sandbox setting changes that.
- **So only two installed tools run outside the sandbox:** `~/.local/bin/fridge-flash` and `fridge-serial`. They're listed under `excludedCommands` in the gitignored `.claude/settings.local.json`.
  - Their sources are `firmware/tools/flash.sh` and `serial.sh`.
  - Claude can't write to `~/.local/bin` (sandbox plus an `Edit(~/.local/bin/**)` deny rule in user settings), so whatever runs unsandboxed is only what the user installed.
  - After a source changes, the user reviews it and reinstalls it: `install -m 755 firmware/tools/flash.sh ~/.local/bin/fridge-flash` (and the same for `serial.sh` → `fridge-serial`).
  - Uploads stay upload-only; compiling never runs unsandboxed.
- **Call the tools alone**, by their absolute path (`/Users/<me>/.local/bin/...`). The exclusion only applies when every command in the call matches, so `diff … && fridge-serial` runs sandboxed and fails.
- `arduino-cli monitor` quits right away when it's run from a script, and reconnecting in a fast loop can hang the board. That's why `serial.sh` uses `stty` and `cat` and pauses between reconnects.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| No `/dev/cu.usbmodem*` port | The board is in deep sleep, and USB is off while it sleeps | Hold B, tap R, then release B for download mode. The buttons are tiny, at the USB-C end of the XIAO; press them with a fingernail or a wooden toothpick, never metal |
| Board gets a 404 and sleeps 60 min | Old firmware still points at the deleted Worker URL | Re-flash. **Re-flash every XIAO after the Worker URL changes**; the spare XIAO may still need it |
| The log looks fine (data fetched, `Sleeping`) but the screen doesn't change | The **ribbon cable has come loose**. It fails silently, with no error | Run `hello_4in26` to confirm. Then, with USB unplugged, flip the latch up, reseat the ribbon straight and fully, press the latch down, and press the XIAO firmly into its socket |
| The port is present but there's no log and the board never sleeps | The board hung partway through a cycle | Tap R |
| Values seem stale | The Worker's KV cache lasts 30 min | Wait, or check the endpoint with curl |

When something breaks, rule out the layers in order: endpoint (curl with the token) → serial log → `hello_4in26` → cables.

## Layout
```
cloud/                     # Cloudflare Worker; .dev.vars (gitignored) holds the secrets
firmware/fridge_4in26/     # main sketch; secrets.h (gitignored) holds Wi-Fi, URL, token
firmware/hello_4in26/      # Seeed HelloWorld screen test
firmware/tools/            # font/icon converter; flash.sh and serial.sh (sources for ~/.local/bin/fridge-*)
firmware/build/            # compile output (gitignored)
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
