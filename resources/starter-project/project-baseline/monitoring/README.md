# Мониторинг и учебные инциденты

## Состав

- `prometheus/prometheus.yml` — шаблон конфигурации сбора метрик API и подключения правил (ЛР8);
- `prometheus/rules.yml` — шаблон учебных сигналов доступности, ошибок и latency (ЛР8);
- `postmortem-template.md` — шаблон расследования;
- `incident-scenarios.md` — назначение подготовленных наборов данных.

Провижининг Grafana и готовый дашборд в студенческий комплект не входят: источник данных и панели проектируются самостоятельно в ЛР8. Оценивается не оформление дашборда, а корректность выбранных сигналов и обоснованность интерпретации.

## Запуск

```bash
cp .env.example .env
docker compose --profile monitoring up -d --build
python scripts/generate_traffic.py --data data/production_normal.csv --rows 200
python scripts/generate_traffic.py --data data/production_drift.csv --rows 200 --invalid-every 25
```

Интерфейсы:

- API — `http://127.0.0.1:8000`;
- Prometheus — `http://127.0.0.1:9090`;
- Grafana — `http://127.0.0.1:3000` (`admin` / значение `GRAFANA_ADMIN_PASSWORD` из локального `.env`).

Пароль не должен фиксироваться в Git. Для учебной локальной среды `.env.example` содержит только заменяемое значение.
