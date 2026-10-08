import os
import requests
import datetime

# =========================
# CONFIG
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SPOTS = [
    {
        "name": "Levanto",
        "lat": 44.17,
        "lon": 9.61,
        "min_height": 0.8,
        "min_period": 7,
        "good_dirs": ["W", "SW", "WSW", "SSW"]
    },
    {
        "name": "Recco",
        "lat": 44.36,
        "lon": 9.15,
        "min_height": 1.2,
        "min_period": 8,
        "good_dirs": ["W", "SW", "WSW"]
    },
]

# =========================
# TELEGRAM
# =========================

def send_alert(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
    )

    print("Telegram status:", response.status_code)
    print(response.text)


# =========================
# UTILS
# =========================

def deg_to_dir(deg):

    dirs = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]

    return dirs[int((deg + 11.25) / 22.5) % 16]


# =========================
# API
# =========================

def get_marine(lat, lon):

    url = (
        "https://marine-api.open-meteo.com/v1/marine?"
        f"latitude={lat}&longitude={lon}"
        "&hourly=wave_height,wave_direction,wave_period"
    )

    return requests.get(url).json()


def get_weather(lat, lon):

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        "&hourly=wind_speed_10m,wind_direction_10m"
    )

    return requests.get(url).json()


# =========================
# SURF CHECK
# =========================

def check_spot(spot):

    print(f"\n🔍 Controllo {spot['name']}")

    marine = get_marine(spot["lat"], spot["lon"])
    weather = get_weather(spot["lat"], spot["lon"])

    if "hourly" not in marine:
        print("❌ Dati marine assenti")
        return

    if "hourly" not in weather:
        print("❌ Dati weather assenti")
        return

    m = marine["hourly"]
    w = weather["hourly"]

    now = datetime.datetime.now(datetime.timezone.utc)

    alert_sent = False

    for h, p, d, ws, wd, ts in zip(
    m["wave_height"],
    m["wave_period"],
    m["wave_direction"],
    w["wind_speed_10m"],
    w["wind_direction_10m"],
    m["time"]
):

    try:
        forecast_time = datetime.datetime.fromisoformat(
            ts.replace("Z", "")
        )
    except Exception:
        continue

    hours_ahead = (
        forecast_time - datetime.datetime.utcnow()
    ).total_seconds() / 3600

    if not (48 <= hours_ahead <= 72):
        continue

    swell_dir = deg_to_dir(d)
    wind_dir = deg_to_dir(wd)

    ws_kt = ws * 0.539957

    offshore = (
        (swell_dir.startswith("W") and wind_dir.startswith("E"))
        or
        (swell_dir.startswith("E") and wind_dir.startswith("W"))
        or
        (swell_dir.startswith("N") and wind_dir.startswith("S"))
        or
        (swell_dir.startswith("S") and wind_dir.startswith("N"))
    )

    good_height = h >= spot["min_height"]
    good_period = p >= spot["min_period"]
    good_direction = swell_dir in spot["good_dirs"]
    good_wind = offshore and ws_kt <= 12

    print(
        f"{spot['name']} | "
        f"{forecast_time} | "
        f"H={h:.2f}m | "
        f"P={p:.1f}s | "
        f"{swell_dir} | "
        f"WIND={wind_dir} {ws_kt:.1f}kt"
    )

    if (
        good_height
        and good_period
        and good_direction
        and good_wind
    ):

        send_alert(
            f"🌊 *Surf Alert - {spot['name']}*\n\n"
            f"📏 Altezza: *{h:.2f} m*\n"
            f"⏱️ Periodo: *{p:.1f} s*\n"
            f"🧭 Swell: *{swell_dir}*\n"
            f"💨 Vento: *{wind_dir}* ({ws_kt:.1f} kt)\n"
            f"📅 {forecast_time.strftime('%d/%m/%Y %H:%M')}\n"
            f"⏳ Tra circa *{int(hours_ahead)} ore*"
        )

        print(f"✅ Alert inviato per {spot['name']}")
        break

    if not alert_sent:
        print(f"❌ Nessuna condizione valida per {spot['name']}")


# =========================
# MAIN
# =========================

def main():

    print("🚀 Avvio Surf Alert Liguria")

    for spot in SPOTS:
        check_spot(spot)

    print("🏁 Controllo terminato")


if __name__ == "__main__":
    main()
