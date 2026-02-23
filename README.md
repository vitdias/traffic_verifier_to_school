# MVP de Alertas de Hora de Sair (Termux + Termux:API + Python)

Sistema de alertas para Android (via **Termux**) que calcula ETA com trânsito em tempo real e avisa quando está na hora de sair para chegar até o horário limite.

## O que este MVP entrega

- Múltiplos alertas configuráveis em `alerts.yaml`.
- Cálculo de ETA via **Google Maps Directions API** (`driving`, `departure_time=now`).
- Destino por **endereço textual** (com geocoding e cache) ou por `lat,lng`.
- Canais de notificação:
  - Telegram Bot API
  - Notificação local Android (`termux-notification`, prioridade alta, som e vibração)
  - Alexa via Voice Monkey (set de volume + TTS)
- Controle anti-spam por alerta/dia (`max_notifications_per_day`, default = 1).
- Retry para falhas de GPS e API de rotas.
- Testes unitários para lógica de disparo e mocks de integração.

---

## Estrutura do projeto

```text
.
├── alerts.example.yaml
├── .env.example
├── requirements.txt
├── scripts/
│   ├── start.sh
│   └── termux_boot.sh
├── src/traffic_alerts/
│   ├── config.py
│   ├── location.py
│   ├── logic.py
│   ├── main.py
│   ├── notify.py
│   ├── notify_alexa.py
│   ├── notify_android.py
│   ├── notify_telegram.py
│   ├── routing.py
│   └── state.py
└── tests/
    ├── test_integration_mocks.py
    └── test_logic.py
```

---

## Requisitos

- Android com Termux instalado.
- App **Termux:API** instalado.
- Python 3.11+ no Termux.
- Chave do Google Maps API com Geocoding API + Directions API habilitadas.
- (Opcional) Bot Telegram.
- (Opcional) Voice Monkey + Alexa configurados.

---

## Instalação no Termux

1. Instale pacotes do Termux:

```bash
pkg update -y
pkg install -y python termux-api git
```

2. Clone projeto e entre no diretório:

```bash
git clone <seu-repo> ~/traffic_verifier_to_school
cd ~/traffic_verifier_to_school
```

3. Crie ambiente virtual e instale dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

4. Configure arquivos de ambiente e alertas:

```bash
cp .env.example .env
cp alerts.example.yaml alerts.yaml
```

---

## Permissões de GPS no Android

- Abra Termux e rode ao menos uma vez:

```bash
termux-location -p gps -r last
```

- Quando o Android pedir, conceda permissão de localização para Termux.
- Se necessário, em configurações do app, permita localização precisa.

---

## Configuração de variáveis de ambiente

Preencha `.env` com suas credenciais:

```ini
GOOGLE_MAPS_API_KEY=...

TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

VOICEMONKEY_TOKEN=...
VOICEMONKEY_DEVICE_ID=...
ALEXA_VOLUME_LEVEL=6
```

> Você pode deixar Telegram/Voice Monkey em branco se o alerta não usar esses canais.

---

## Configuração dos alertas (`alerts.yaml`)

Cada alerta suporta:

- `destination`: endereço textual **ou** `lat,lng`.
- `latest_arrival_time`: horário limite para chegar (`HH:MM`).
- `notify_buffer_minutes`: quando `slack <= buffer`, dispara.
- `schedule_days`: dias ativos (`MON..SUN`).
- `active_window_start` e `active_window_end`: janela diária de checagem.
- `poll_seconds`: frequência de checagem do alerta.
- `channels`: `telegram`, `android_notification`, `alexa_voice`.
- `label`: nome amigável.
- `timezone` opcional por alerta (default global).
- `max_notifications_per_day` opcional (default 1).
- `message_template` opcional, para customizar texto facilmente.

Regra:

- `deadline = hoje + latest_arrival_time`
- `eta_now = duração de carro com trânsito`
- `slack = deadline - now - eta_now`
- se `slack <= notify_buffer_minutes` → notifica
- se `now > deadline` dentro da janela ativa → dispara alerta de atraso

Template default:

```text
[{label}] ETA agora: {eta_minutes} min. Folga: {slack_minutes} min. Horário limite: {latest_arrival_time}.
```

Placeholders disponíveis: `{label}`, `{eta_minutes}`, `{slack_minutes}`, `{latest_arrival_time}`, `{destination}`, `{notify_buffer_minutes}`.

---

## Telegram Bot

1. Crie bot com BotFather e pegue token.
2. Obtenha o `chat_id` (ex: enviando mensagem ao bot e consultando `getUpdates`).
3. Configure `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.

---

## Voice Monkey + Alexa (Echo Studio)

1. Habilite a Skill Voice Monkey na sua conta Alexa.
2. Crie/registre device/rotina conforme painel do Voice Monkey.
3. Copie `VOICEMONKEY_TOKEN` e `VOICEMONKEY_DEVICE_ID` para `.env`.
4. Ajuste `ALEXA_VOLUME_LEVEL` (0 a 10).

Fluxo de alerta Alexa no código:

1. tenta ajustar volume,
2. envia TTS com a mesma mensagem do Telegram/Android.

Se o ajuste de volume falhar, o sistema ainda tenta falar.

> Observação: o Voice Monkey pode ter limites de uso/quota dependendo do plano. Em picos, falhas HTTP devem aparecer em log.

---

## Execução manual

```bash
source .venv/bin/activate
export PYTHONPATH=$PWD/src
python -m traffic_alerts.main
```

---

## Autostart no boot (Termux:Boot + loop)

1. Instale app **Termux:Boot** no Android.
2. Crie a pasta de boot do Termux:

```bash
mkdir -p ~/.termux/boot
```

3. Copie o script de boot:

```bash
cp scripts/termux_boot.sh ~/.termux/boot/traffic_alerts_boot.sh
chmod +x ~/.termux/boot/traffic_alerts_boot.sh
```

4. Reinicie o celular para validar.

O script de boot executa loop contínuo e reinicia o processo em caso de falha, gravando logs em `logs/traffic_alerts.log`.

---

## Exemplo de scheduler alternativo (Termux Job Scheduler)

Se preferir disparo periódico em vez de daemon contínuo:

```bash
termux-job-scheduler --job-id 9001 --period-ms 900000 --script "$HOME/traffic_verifier_to_school/scripts/start.sh"
```

---

## Testes

```bash
export PYTHONPATH=$PWD/src
pytest -q
```

---

## Observações operacionais

- APIs externas podem oscilar; há retry para GPS e rotas.
- Geocoding de endereço é cacheado em `data/geocode_cache.json`.
- Estado anti-spam é salvo em `data/state.json`.
- Para ajustar rapidamente o texto falado/enviado, altere `message_template` no YAML (global ou por alerta).
