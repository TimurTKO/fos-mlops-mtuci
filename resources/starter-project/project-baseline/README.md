# Базовый учебный ML-проект — студенческий каркас

Проект является технической базой лабораторного практикума. В студенческом комплекте сохранены структура каталогов, публичные интерфейсы модулей и постановка задачи, а реализация вынесена в задания лабораторных работ и помечена комментариями `TODO`.

Целевой контур, который выстраивается последовательно от ЛР1 к ЛР9:

> генерация данных → DVC → обучение и оценка → MLflow → API → контейнеризация → smoke-проверка → обновление/откат → Prometheus/Grafana → drift → расследование инцидента → CI.

## Что уже готово

- исходный исследовательский прототип [`notebooks/01_ml_prototype.ipynb`](notebooks/01_ml_prototype.ipynb);
- воспроизводимый генератор данных [`scripts/generate_data.py`](scripts/generate_data.py);
- контракт данных [`configs/data_contract.json`](configs/data_contract.json);
- шаблоны параметров [`params.yaml`](params.yaml) и окружения [`.env.example`](.env.example);
- зависимости [`pyproject.toml`](pyproject.toml), [`requirements.txt`](requirements.txt), [`requirements-mlops.txt`](requirements-mlops.txt);
- шаблоны политики выпуска и постмортема в [`deployment/`](deployment/release-policy-template.md) и [`monitoring/`](monitoring/postmortem-template.md);
- описание учебных сценариев инцидентов [`monitoring/incident-scenarios.md`](monitoring/incident-scenarios.md).

## Что предстоит реализовать

| Файл | Лабораторная работа |
|---|---|
| `src/mlops_course/data.py`, `train.py`, `predict.py` | ЛР1 |
| `tests/` | ЛР2 |
| `.github/workflows/ci.yml` | ЛР3 |
| `dvc.yaml` | ЛР4 |
| `scripts/run_experiments.py` | ЛР5 |
| `src/mlops_course/api.py`, `Dockerfile`, `compose.yaml`, `scripts/smoke_test.py` | ЛР6 |
| `scripts/release_manager.py` | ЛР7 |
| `src/mlops_course/monitoring.py`, `monitoring/prometheus/`, `scripts/generate_traffic.py`, `scripts/analyze_drift.py` | ЛР8 |
| `scripts/investigate_incident.py` | ЛР9 |

Каркас содержит сигнатуры функций, docstring с ожидаемым поведением и `TODO` со ссылкой на соответствующую работу. Менять имена модулей, функций и их параметры не требуется: на них опираются задания и критерии оценивания.

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
```

Дальнейшие команды становятся работоспособными по мере выполнения лабораторных работ:

```bash
python -m mlops_course.train                  # после ЛР1
pytest                                        # после ЛР2
uvicorn mlops_course.api:app --reload         # после ЛР6
```

Проверка API после ЛР6: `curl http://127.0.0.1:8000/health`.

## Модуль 2: DVC и MLflow

```bash
python -m pip install -e ".[all]"
dvc init
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

Требования к выпуску и откату: [`deployment/README.md`](deployment/README.md).

## Модуль 4: мониторинг, drift и инциденты

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
monitoring/           Prometheus, правила, сценарии и постмортем
tests/                проверки кода, данных, модели, API и конфигураций
data/                 генерируемые версии данных
artifacts/            модель и метрики
Dockerfile             контейнер API
compose.yaml           API, smoke, Prometheus и Grafana
deployment/            требования к выпуску и политика отката
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
