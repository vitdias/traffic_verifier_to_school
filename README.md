
# Car-to-School Travel Time Notifier

A Python-based scheduler that retrieves driving ETA from your home to your child’s school every weekday around 17:30, then sends out notifications (via WhatsApp or TickTick) reporting arrival times for departures at 18:00, 17:50, and 17:40.

## 🚀 Features
- **Automated Scheduling**  
  Runs every Monday–Friday near school time using Apache Airflow.
- **Travel Time Lookup**  
  Queries Google Maps (or other provider) for ETA at somespecified departure times.
- **Multi-Channel Notifications**  
  - **WhatsApp** (via Twilio trial or other free API)  
  - **TickTick** task reminder (via TickTick’s API)
- **Containerized**  
  Entire stack runs in Docker for reproducible deployments.

## 🏗️ Architecture Overview
┌──────────┐ ┌─────────────┐ ┌────────────┐ ┌───────────────┐
│ Airflow │──▶ │ Python ETL │──▶ │ Maps API │──▶ │ Notification │
│ Scheduler│ │ (fetch ETA) │ │ (Google) │ │ (WhatsApp / │
│ (Docker) │ └─────────────┘ └────────────┘ │ TickTick) │
└──────────┘ └───────────────┘


## 📋 Prerequisites
- Docker & Docker Compose  
- Google Maps API key (or alternative routing API)  
- Twilio account for WhatsApp (trial credentials) **or** TickTick API token  
- Python 3.9+

## 🛠️ Installation & Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/<your-username>/car-travel-time-notifier.git
   cd car-travel-time-notifier

2. Configure environment
Copy .env.example to .env and fill in your keys:

```ini
GOOGLE_MAPS_API_KEY=your_google_maps_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_FROM=whatsapp:+1415XXXXXXX
TWILIO_WHATSAPP_TO=whatsapp:+55XXXXXXXXX
TICKTICK_API_TOKEN=your_ticktick_token
HOME_ADDRESS="Rua Exemplo, 123, São Paulo, Brazil"
SCHOOL_ADDRESS="Av. Escola, 456, São Paulo, Brazil"
```
3. Start Docker services

```bash
docker-compose up -d
airflow-scheduler, airflow-webserver, airflow-postgres, and airflow-redis will spin up.
```
4. Initialize Airflow

```bash
docker-compose exec airflow-webserver airflow db init
docker-compose exec airflow-webserver airflow users create \
  --username admin --password admin --firstname Admin --lastname User --role Admin --email you@example.com
```

5. Access Airflow UI
Go to http://localhost:8080 and confirm the car_travel_time_dag.py DAG is listed and unpaused.

