from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from traffic_alerts.config import load_app_config, load_env
from traffic_alerts.location import get_current_location
from traffic_alerts.logic import evaluate_alert
from traffic_alerts.notify import build_message, notify_channels
from traffic_alerts.routing import GoogleRoutingClient
from traffic_alerts.state import StateStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("traffic_alerts")


def run_forever() -> None:
    env = load_env()
    app_cfg = load_app_config()
    state = StateStore(app_cfg.state_file)
    router = GoogleRoutingClient(env.google_maps_api_key, app_cfg.geocode_cache_file)

    if not app_cfg.alerts:
        logger.warning("Nenhum alerta configurado")
        return

    base_sleep = max(15, min(alert.poll_seconds for alert in app_cfg.alerts))
    last_checked: dict[str, float] = {alert.label: 0.0 for alert in app_cfg.alerts}

    while True:
        now_ts = time.time()
        now_utc = datetime.now(timezone.utc)

        due_alerts = [
            alert
            for alert in app_cfg.alerts
            if now_ts - last_checked.get(alert.label, 0.0) >= alert.poll_seconds
        ]

        if not due_alerts:
            time.sleep(base_sleep)
            continue

        try:
            origin = get_current_location(max_retries=3, retry_delay_seconds=3)
        except Exception:
            logger.exception("Falha ao obter GPS no ciclo. Tentará novamente no próximo ciclo.")
            time.sleep(base_sleep)
            continue

        for alert in due_alerts:
            last_checked[alert.label] = now_ts
            try:
                eta = router.get_eta_in_traffic(origin=origin, destination=alert.destination, max_retries=3)
                evaluation = evaluate_alert(alert, now_utc, eta.eta_seconds)

                logger.info(
                    "Alerta=%s evaluate=%s notify=%s reason=%s slack_min=%s eta_min=%s",
                    alert.label,
                    evaluation.should_evaluate,
                    evaluation.should_notify,
                    evaluation.reason,
                    evaluation.slack_minutes,
                    evaluation.eta_minutes,
                )

                if not evaluation.should_evaluate or not evaluation.should_notify:
                    continue

                local_day = now_utc.astimezone(ZoneInfo(alert.timezone)).date()
                if not state.can_notify(alert.label, local_day, alert.max_notifications_per_day):
                    logger.info("Alerta=%s já atingiu limite diário", alert.label)
                    continue

                message = build_message(alert, evaluation.eta_minutes, evaluation.slack_minutes)
                notify_channels(alert, env, message)
                state.mark_notified(alert.label, local_day)
                logger.info("Notificação enviada para alerta=%s", alert.label)
            except Exception:
                logger.exception("Falha no processamento do alerta=%s", alert.label)

        time.sleep(base_sleep)


if __name__ == "__main__":
    run_forever()
