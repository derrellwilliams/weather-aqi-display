// Fridge display data endpoint (Cloudflare Worker).
// Returns ready-to-draw values so the device only places text and icons:
// {greeting, date, temp, hi, lo, precip_icon, precip_label, aqi, aqi_label, aqi_pos,
//  hours: [{t, icon, label}], sleep_min}
// Secrets/vars: PURPLEAIR_API_KEY, LAT, LON, DEVICE_TOKEN. Optional KV binding: CACHE.

const RADIUS_MI = 5;
const CACHE_SECONDS = 30 * 60;
const CACHE_KEY = "fridge-raw-v2";
const NIGHT_START_HOUR = 23; // sleep after the 11:01 pm update...
const NIGHT_END_HOUR = 4; // ...until 4:01 am

export default {
  async fetch(request, env) {
    if (!authorized(request, env)) {
      return new Response("Unauthorized", { status: 401 });
    }

    let raw = env.CACHE ? await env.CACHE.get(CACHE_KEY, "json") : null;
    if (!raw) {
      raw = await fetchRaw(env);
      if (!raw) return new Response("Upstream error", { status: 502 });
      // Only cache complete results, so a failed upstream is retried next time.
      if (env.CACHE && raw.air && raw.weather) {
        await env.CACHE.put(CACHE_KEY, JSON.stringify(raw), { expirationTtl: CACHE_SECONDS });
      }
    }

    // Labels are built per request from the cached data, so times stay current.
    return new Response(JSON.stringify(buildView(raw, new Date())), {
      headers: { "Content-Type": "application/json" },
    });
  },
};

function authorized(request, env) {
  if (!env.DEVICE_TOKEN) return false; // fail closed if the token isn't configured
  const url = new URL(request.url);
  const header = request.headers.get("Authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : url.searchParams.get("token");
  return token === env.DEVICE_TOKEN;
}

async function fetchRaw(env) {
  const lat = Number(env.LAT);
  const lon = Number(env.LON);
  const [air, weather] = await Promise.allSettled([
    getAir(lat, lon, env.PURPLEAIR_API_KEY),
    getWeather(lat, lon),
  ]);
  if (air.status === "rejected") console.error("PurpleAir:", air.reason);
  if (weather.status === "rejected") console.error("Open-Meteo:", weather.reason);
  if (air.status === "rejected" && weather.status === "rejected") return null;
  return {
    air: air.status === "fulfilled" ? air.value : null,
    weather: weather.status === "fulfilled" ? weather.value : null,
  };
}

// ---------- Screen view ----------

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function buildView(raw, nowUtc) {
  const w = raw.weather;
  // Shift to local time using Open-Meteo's offset, then read with getUTC* methods.
  // Without weather data, fall back to Mountain Standard Time.
  const offset = w ? w.utc_offset_seconds : -7 * 3600;
  const local = new Date(nowUtc.getTime() + offset * 1000);
  const hour = local.getUTCHours();
  const minute = local.getUTCMinutes();

  const view = {
    greeting: greeting(hour),
    date: `${MONTHS[local.getUTCMonth()]} ${ordinal(local.getUTCDate())}`,
    sleep_min: sleepMinutes(hour, minute),
    temp: null,
    hi: null,
    lo: null,
    precip_icon: "",
    precip_label: "",
    aqi: null,
    aqi_label: "AQI · NO DATA",
    aqi_pos: 0,
    hours: [],
  };

  if (raw.air) {
    view.aqi = raw.air.aqi;
    view.aqi_label = `AQI · ${shortCategory(raw.air.aqi)}`;
    view.aqi_pos = aqiPosition(raw.air.aqi);
  }

  if (w) {
    const d = w.daily;
    view.temp = Math.round(w.current.temperature_2m);
    view.hi = Math.round(d.temperature_2m_max[0]);
    view.lo = Math.round(d.temperature_2m_min[0]);

    const pct = d.precipitation_probability_max[0] ?? 0;
    const inches = d.precipitation_sum[0] ?? 0;
    const type = precipType(d.weather_code[0], d.snowfall_sum[0]);
    if (type === "none" && pct < 30) {
      view.precip_label = `${pct}% Precip Today`;
    } else {
      view.precip_icon = type === "snow" ? "snowflake" : "drop";
      view.precip_label =
        `${type === "snow" ? "SNOW" : "RAIN"} ${pct}%` + (inches > 0 ? ` · ${inches.toFixed(2)} IN` : "");
    }

    // Next 7 hours, starting at the next full hour. Open-Meteo times are local "YYYY-MM-DDTHH:MM".
    const nowStr = local.toISOString().slice(0, 16);
    const h = w.hourly;
    const start = h.time.findIndex((t) => t > nowStr);
    for (let i = start; i >= 0 && i < h.time.length && view.hours.length < 7; i++) {
      const hr = Number(h.time[i].slice(11, 13));
      view.hours.push({
        t: Math.round(h.temperature_2m[i]),
        icon: weatherIcon(h.weather_code[i], h.is_day[i] === 1),
        label: `${hr % 12 === 0 ? 12 : hr % 12}${hr < 12 ? "AM" : "PM"}`,
      });
    }
  }
  return view;
}

function greeting(hour) {
  if (hour >= 5 && hour < 12) return "Good Morning!";
  if (hour >= 12 && hour < 17) return "Good Afternoon!";
  if (hour >= 17 && hour < 22) return "Good Evening!";
  return "Good Night!";
}

function ordinal(n) {
  const teen = n % 100 >= 11 && n % 100 <= 13;
  const suffix = teen ? "th" : { 1: "st", 2: "nd", 3: "rd" }[n % 10] || "th";
  return `${n}${suffix}`;
}

// Wake a minute past each hour; skip the night entirely.
function sleepMinutes(hour, minute) {
  const nowMin = hour * 60 + minute;
  if (hour >= NIGHT_START_HOUR || hour < NIGHT_END_HOUR) {
    return (NIGHT_END_HOUR * 60 + 1 - nowMin + 24 * 60) % (24 * 60);
  }
  return 61 - minute;
}

// Phosphor icon names; the firmware has a bitmap for each.
function weatherIcon(code, isDay) {
  if (code <= 1) return isDay ? "sun" : "moon-stars";
  if (code === 2) return isDay ? "cloud-sun" : "cloud-moon";
  if (code === 3) return "cloud";
  if (code === 45 || code === 48) return "cloud-fog";
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "cloud-snow";
  if (code >= 95) return "cloud-lightning";
  if (code >= 51 && code <= 82) return "cloud-rain";
  return "cloud";
}

// WMO weather codes: 71-77 and 85-86 are snow; 51-67, 80-82 and 95-99 are rain.
function precipType(code, snowIn) {
  if (snowIn > 0 || (code >= 71 && code <= 77) || code === 85 || code === 86) return "snow";
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82) || code >= 95) return "rain";
  return "none";
}

// ---------- Air quality (PurpleAir) ----------

async function getAir(lat, lon, apiKey) {
  if (!apiKey) throw new Error("PURPLEAIR_API_KEY not set");

  // Bounding box slightly larger than the circle; the haversine filter trims the corners.
  const dLat = RADIUS_MI / 69.0;
  const dLon = RADIUS_MI / (69.0 * Math.cos((lat * Math.PI) / 180));
  const params = new URLSearchParams({
    // pm2.5_cf_1 is what the EPA correction formula was built on.
    fields: "pm2.5_cf_1,humidity,latitude,longitude",
    location_type: "0", // outdoor only
    max_age: "3600", // skip sensors silent for over an hour
    nwlat: String(lat + dLat),
    nwlng: String(lon - dLon),
    selat: String(lat - dLat),
    selng: String(lon + dLon),
  });

  const res = await fetch(`https://api.purpleair.com/v1/sensors?${params}`, {
    headers: { "X-API-Key": apiKey },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  const { fields, data } = await res.json();

  const col = (name) => fields.indexOf(name);
  const iPm = col("pm2.5_cf_1");
  const iRh = col("humidity");
  const iLat = col("latitude");
  const iLon = col("longitude");

  const readings = [];
  for (const row of data) {
    const pm = row[iPm];
    const rh = row[iRh];
    if (pm == null || rh == null || pm < 0 || pm > 1000) continue; // missing or broken sensor
    if (milesBetween(lat, lon, row[iLat], row[iLon]) > RADIUS_MI) continue;
    readings.push(epaCorrect(pm, rh));
  }
  if (readings.length === 0) throw new Error("No sensors within range");

  const avgPm = readings.reduce((a, b) => a + b, 0) / readings.length;
  return { aqi: pmToAqi(avgPm), sensors: readings.length };
}

function milesBetween(lat1, lon1, lat2, lon2) {
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * 3958.8 * Math.asin(Math.sqrt(a));
}

// US EPA correction for PurpleAir (Barkjohn et al., extended for smoke).
function epaCorrect(pm, rh) {
  let out;
  if (pm < 30) {
    out = 0.524 * pm - 0.0862 * rh + 5.75;
  } else if (pm < 50) {
    const w = pm / 20 - 3 / 2;
    out = (0.786 * w + 0.524 * (1 - w)) * pm - 0.0862 * rh + 5.75;
  } else if (pm < 210) {
    out = 0.786 * pm - 0.0862 * rh + 5.75;
  } else if (pm < 260) {
    const w = pm / 50 - 21 / 5;
    out =
      (0.69 * w + 0.786 * (1 - w)) * pm -
      0.0862 * rh * (1 - w) +
      2.966 * w +
      5.75 * (1 - w) +
      8.84e-4 * pm * pm * w;
  } else {
    out = 2.966 + 0.69 * pm + 8.84e-4 * pm * pm;
  }
  return Math.max(0, out);
}

// 2024 EPA PM2.5 breakpoints: [pmLow, pmHigh, aqiLow, aqiHigh].
const BREAKPOINTS = [
  [0.0, 9.0, 0, 50],
  [9.1, 35.4, 51, 100],
  [35.5, 55.4, 101, 150],
  [55.5, 125.4, 151, 200],
  [125.5, 225.4, 201, 300],
  [225.5, 325.4, 301, 500],
];

function pmToAqi(pm) {
  const c = Math.floor(pm * 10) / 10; // EPA truncates to one decimal
  for (const [cLo, cHi, iLo, iHi] of BREAKPOINTS) {
    if (c <= cHi) return Math.round(((iHi - iLo) / (cHi - cLo)) * (Math.max(c, cLo) - cLo) + iLo);
  }
  return 500;
}

// The screen's bar has 6 equal segments, one per AQI category.
const AQI_BANDS = [
  [0, 50, "GOOD"],
  [51, 100, "MODERATE"],
  [101, 150, "SENSITIVE GROUPS"],
  [151, 200, "UNHEALTHY"],
  [201, 300, "VERY UNHEALTHY"],
  [301, 500, "HAZARDOUS"],
];

function shortCategory(aqi) {
  return (AQI_BANDS.find(([, hi]) => aqi <= hi) || AQI_BANDS[5])[2];
}

// 0..1 position of the marker along the bar.
function aqiPosition(aqi) {
  let i = AQI_BANDS.findIndex(([, hi]) => aqi <= hi);
  if (i === -1) i = 5;
  const [lo, hi] = AQI_BANDS[i];
  const frac = Math.min(1, Math.max(0, (aqi - lo) / (hi - lo)));
  return Math.round(((i + frac) / 6) * 1000) / 1000;
}

// ---------- Weather (Open-Meteo, no key) ----------

async function getWeather(lat, lon) {
  const params = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lon),
    current: "temperature_2m",
    hourly: "temperature_2m,weather_code,is_day",
    daily:
      "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,snowfall_sum,weather_code",
    temperature_unit: "fahrenheit",
    precipitation_unit: "inch",
    timezone: "auto",
    forecast_days: "2", // tomorrow's hours are needed late in the day
  });
  const res = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  const j = await res.json();
  // Keep only what buildView needs, so the KV entry stays small.
  return { utc_offset_seconds: j.utc_offset_seconds, current: j.current, hourly: j.hourly, daily: j.daily };
}
