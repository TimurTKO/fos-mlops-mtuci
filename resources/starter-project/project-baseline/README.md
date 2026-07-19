# Базовый учебный ML-проект

Проект является рабочим техническим ресурсом лабораторного практикума и реализует полный учебный контур:

> генерация данных → DVC → обучение и оценка → MLflow → API → контейнеризация → smoke-проверка → обновление/откат → Prometheus/Grafana → drift → расследование инцидента → CI.

Для студенческой выдачи преподаватель может удалить готовые инженерные элементы или пометить их `TODO`, сохранив исходный ноутбук, контракт и постановку задачи.

## Требования

- Python 3.11+;
- CPU; GPU не требуется;
- Git;
- для модуля 2 — DVC 3.x и MLflow 3.x;
- для модулей 3–4 — Docker Engine / Docker Desktop и Docker Compose;
- Windows, Linux или macOS.

## Базовая установка

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
python scripts/generate_data.py --output-dir data
python -m mlops_course.train
pytest
uvicorn mlops_course.api:app --reload
```

Проверка API: `curl http://127.0.0.1:8000/health`.

## Модуль 2: DVC и MLflow

```bash
python -m pip install -e ".[all]"
dvc repro
dvc metrics show
python scripts/run_experiments.py
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

## Модуль 3: Docker Compose и выпуск

```bash
cp .env.example .env
docker compose config
docker compose build api
docker compose up -d api
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
python scripts/release_manager.py --help
```

Подробности: [`deployment/README.md`](deployment/README.md).

## Модуль 4: мониторинг, drift и инциденты

Запуск всего контура:

```bash
cp .env.example .env
docker compose --profile monitoring up -d --build
python scripts/generate_traffic.py --data data/production_normal.csv --rows 200
python scripts/generate_traffic.py --data data/production_drift.csv --rows 200 --invalid-every 25
```

Анализ данных и качества:

```bash
python scripts/analyze_drift.py   --reference data/production_normal.csv   --current data/production_drift.csv   --output-dir reports/drift
```

Расследование сценария:

```bash
python scripts/investigate_incident.py   --reference data/production_normal.csv   --current data/incident_degraded.csv   --output-dir reports/incident
```

Интерфейсы: API `:8000`, Prometheus `:9090`, Grafana `:3000`. Конфигурации и описание сценариев находятся в [`monitoring/`](monitoring/README.md).

## Структура

```text
configs/              контракт данных
notebooks/            исходный исследовательский прототип
scripts/              данные, эксперименты, трафик, drift, инциденты и релизы
src/mlops_course/     данные, обучение, инференс, API и метрики
monitoring/           Prometheus, Grafana, дашборд, правила и постмортем
tests/                проверки кода, данных, модели, API и конфигураций
data/                 генерируемые версии данных
artifacts/            модель и метрики
Dockerfile             контейнер API
compose.yaml           API, smoke, Prometheus и Grafana
deployment/            архитектура и политика выпуска
dvc.yaml               граф воспроизводимого пайплайна
params.yaml             параметры данных и обучения
.github/workflows/      пример CI
```

## Назначение сценариев данных

- `production_normal.csv` — штатная работа;
- `production_drift.csv` — изменение распределения без обязательной деградации;
- `incident_degraded.csv` — снижение качества, которое может не обнаруживаться одномерным PSI;
- `incident_bad_schema.csv` — нарушение контракта данных.

## Что не публикуется в Git

Сгенерированные `data/`, `artifacts/`, `reports/`, DVC cache, локальные MLflow-хранилища, `.env`, секреты, журналы релизов и тома Docker.
