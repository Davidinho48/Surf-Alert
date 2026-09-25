import os
import requests
import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📍 Spot configurati (Liguria + Toscana)
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
    {
        "name": "Marinella di Sarzana",
        "lat": 44.07,
        "lon": 9.97,
        "min_height": 0.7,
        "min_period": 7,
        "good_dirs": ["S", "SSW", "SW"]
    },
    {
        "name": "Varazze",
        "lat": 44.36,
        "lon": 8.59,
        "min_height": 1.0,
        "min_period": 8,
        "good_dirs": ["SW", "WSW", "W"]
    },
    {
        "name": "Marina di Pisa",
        "lat": 43.55,
        "lon": 10.28,
        "min_height": 0.7,
        "min_period": 7,
        "good_dirs": ["SW", "W", "WSW"]
    },
    {
        "name": "Viareggio",
        "lat": 43.87,
        "lon": 10.24,
        "min_height": 0.7,
        "min_period": 7,
        "good_dirs": ["SW", "W", "WSW"]
    },
    {
        "name": "Forte dei Marmi",
        "lat": 43.96,
        "lon": 10.17,
        "min_height": 0.7,
        "min_period": 7,
        "good_dirs": ["SW", "W", "WSW"]
    }
]

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def deg_to_dir(deg):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    ix = int((deg + 11.25) / 22.5) % 16
    return dirs[ix]

def get_forecast(lat, lon):
    url = (
        "https://marine-api.open-meteo.com/v1/marine?"
        f"latitude={lat}&longitude={lon}"
        "&hourly=wave_height,wave_direction,wave_period,wind_speed,wind_direction"
    )
    response = requests.get(url)
    return response.json()

def check_spot(spot):
    print(f"🔍 Controllo spot: {spot['name']}")

    data = get_forecast(spot["lat"], spot["lon"])
    hourly = data["hourly"]

    heights = hourly["wave_height"]
    periods = hourly["wave_period"]
    dirs = hourly["wave_direction"]
    wind_speed = hourly["wind_speed"]
    wind_dir = hourly["wind_direction"]
    timestamps = hourly["time"]

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
                message = (
                    f"🌊 *Onde in arrivo a {spot['name']}!*\n"
                    f"📏 Altezza: *{h:.2f} m*\n"
                    f"⏱️ Periodo: *{p:.1f} s*\n"
                    f"🧭 Swell: *{swell_dir}*\n"
                    f"💨 Vento: *{wind_dir_card}* ({ws} kt) "
                    f"{'*OFFSHORE*' if offshore else 'onshore'}\n"
                    f"📅 {forecast_time.strftime('%A %d %B alle %H:%M')}\n"
                    f"⏳ Previsione entro *{int(hours_ahead)} ore*\n"
                    f"✔️ *Condizioni surfabili (modello Open‑Meteo)*"
                )
                send_alert(message)
                print(f"✔️ Notifica inviata per {spot['name']}")
            else:
                print(f"❌ {spot['name']} non surfabile (48–72h)")

def main():
    print("🚀 Avvio controllo avanzato onde (Open‑Meteo)...")
    for spot in SPOTS:
        check_spot(spot)
    print("🏁 Controllo completato.")

if __name__ == "__main__":
    main()
