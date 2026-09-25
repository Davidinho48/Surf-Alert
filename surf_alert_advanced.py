import os
import requests
import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SPOTS = [
    {"name": "Levanto", "lat": 44.17, "lon": 9.61, "min_height": 0.8, "min_period": 7, "good_dirs": ["W","SW","WSW","SSW"]},
    {"name": "Recco", "lat": 44.36, "lon": 9.15, "min_height": 1.2, "min_period": 8, "good_dirs": ["W","SW","WSW"]},
]

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

def deg_to_dir(deg):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[int((deg + 11.25) / 22.5) % 16]

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

def check_spot(spot):
    print(f"🔍 Controllo spot: {spot['name']}")

    marine = get_marine(spot["lat"], spot["lon"])
    weather = get_weather(spot["lat"], spot["lon"])

    if "hourly" not in marine or "hourly" not in weather:
        print(f"⚠️ Nessun dato disponibile per {spot['name']}")
        return

    m = marine["hourly"]
    w = weather["hourly"]

    heights = m["wave_height"]
    periods = m["wave_period"]
    dirs = m["wave_direction"]
    wind_speed = w["wind_speed_10m"]
    wind_dir = w["wind_direction_10m"]
    timestamps = m["time"]

    now = datetime.datetime.utcnow()

    for h, p, d, ws, wd, ts in zip(heights, periods, dirs, wind_speed, wind_dir, timestamps):
        forecast_time = datetime.datetime.fromisoformat(ts)
        hours_ahead = (forecast_time - now).total_seconds() / 3600

        if 48 <= hours_ahead <= 72:
            swell_dir = deg_to_dir(d)
            wind_dir_card = deg_to_dir(wd)

            offshore = (
                (swell_dir.startswith("W") and wind_dir_card.startswith("E")) or
                (swell_dir.startswith("E") and wind_dir_card.startswith("W")) or
                (swell_dir.startswith("S") and wind_dir_card.startswith("N")) or
                (swell_dir.startswith("N") and wind_dir_card.startswith("S"))
            )

            good_height = h >= spot["min_height"]
            good_period = p >= spot["min_period"]
            good_direction = swell_dir in spot["good_dirs"]
            good_wind = offshore and ws <= 12

            if good_height and good_period and good_direction and good_wind:
                send_alert(
                    f"🌊 *Onde in arrivo a {spot['name']}!*\n"
                    f"📏 Altezza: *{h:.2f} m*\n"
                    f"⏱️ Periodo: *{p:.1f} s*\n"
                    f"🧭 Swell: *{swell_dir}*\n"
                    f"💨 Vento: *{wind_dir_card}* ({ws} kt) {'OFFSHORE' if offshore else 'onshore'}\n"
                    f"📅 {forecast_time.strftime('%A %d %B alle %H:%M')}\n"
                    f"⏳ Previsione entro *{int(hours_ahead)} ore*"
                )
                print(f"✔️ Notifica inviata per {spot['name']}")
            else:
                print(f"❌ {spot['name']} non surfabile (48–72h)")

def main():
    print("🚀 Avvio controllo avanzato onde (Open‑Meteo combinato)...")
    for spot in SPOTS:
        check_spot(spot)
    print("🏁 Controllo completato.")

if __name__ == "__main__":
    main()
