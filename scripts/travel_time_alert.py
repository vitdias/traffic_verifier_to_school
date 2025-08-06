import os, datetime, pytz
import googlemaps
from dotenv import load_dotenv
from notifier import notify_telegram, notify_ticktick, notify_whatsapp

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),"../config/.env"))

# configurações
tz = pytz.timezone("America/Sao_Paulo")
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
origin = os.getenv("ORIGIN")
destination = os.getenv("DESTINATION")

# horários de partida
today = datetime.datetime.now(tz).date()
departure_times = [
    datetime.datetime.combine(today, datetime.time(17,40), tzinfo=tz),
    datetime.datetime.combine(today, datetime.time(17,50), tzinfo=tz),
    datetime.datetime.combine(today, datetime.time(18, 0), tzinfo=tz),
]

messages = []
for dt in departure_times:
    res = gmaps.distance_matrix(
        origins=origin,
        destinations=destination,
        mode="driving",
        departure_time=int(dt.timestamp()),
        traffic_model="best_guess"
    )
    elem = res["rows"][0]["elements"][0]
    dur_text = elem["duration_in_traffic"]["text"]
    dur_sec  = elem["duration_in_traffic"]["value"]
    arrival = dt + datetime.timedelta(seconds=dur_sec)
    messages.append(
        f"Saída {dt.strftime('%H:%M')} → duração {dur_text} → chegada ~{arrival.strftime('%H:%M')}"
    )

body = "🚗 Previsão de Tráfego:\n" + "\n".join(messages)

# notificar pelas opções desejadas:
notify_telegram(body)
# notify_ticktick(body)
# notify_whatsapp(body)
