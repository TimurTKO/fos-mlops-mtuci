# Интеграционный smoke-test преподавательского стенда

Документ фиксирует результат фактического интеграционного прогона полного эталонного проекта. Все приведённые команды выполнялись, все значения получены из вывода этих команд. Предположительные или смоделированные результаты в документ не вносились.

Документ относится к полной преподавательской версии и в студенческую поставку не включается.

Смежные материалы: [runbook](../teachers/course-runbook.md), [диагностика типовых проблем](../teachers/troubleshooting.md), [README эталонного проекта](../../resources/starter-project/project-baseline/README.md).

## 1. Условия прогона

- Дата прогона: **2026-07-28**.
- Проверяемая версия: ветка `feat/teacher-runbook-and-integration-smoke`, коммит `d6918b97e6a5b876874001029d7fedfcbd71d496`.
- Рабочий каталог для команд проекта: `resources/starter-project/project-baseline`.
- `compose.yaml`, `Dockerfile`, конфигурации мониторинга и код эталонного проекта в ходе прогона не изменялись.
- MLflow проверялся отдельно от Docker Compose: сервис MLflow в `compose.yaml` не предусмотрен, и добавлен не был.

### Окружение

| Компонент | Значение |
|---|---|
| Docker Client | 29.6.2, API 1.55, windows/amd64, context `desktop-linux` |
| Docker Server | Docker Desktop 4.83.0 (234302), Engine 29.6.2, API 1.55 |
| containerd / runc | v2.2.5 / 1.3.6 |
| Docker Compose | v5.3.1 |
| OSType / Architecture | linux / x86_64 |
| CPUs / Total Memory | 16 / 15.18 GiB |
| Python | 3.12.0 |
| MLflow / DVC | 3.14.0 / 3.67.1 |

Предварительные условия: порты `8000`, `9090`, `3000` и `5000` свободны; посторонних контейнеров проекта нет; рабочее дерево Git чистое.

## 2. Сценарий

| Шаг | Проверяемое утверждение |
|---:|---|
| 1 | Конфигурация Compose корректна и разрешает переменные из `.env` |
| 2 | Образ API собирается из чистого контекста |
| 3 | Профиль `monitoring` поднимает API, Prometheus и Grafana; API достигает состояния healthy |
| 4 | `/health`, `/ready`, `/docs` и `/metrics` доступны и возвращают ожидаемые схемы |
| 5 | `/predict` обрабатывает валидный запрос и отклоняет невалидный кодом 4xx |
| 6 | Prometheus собирает метрики API, правила загружены |
| 7 | Grafana доступна, источник данных и дашборд подключены провижинингом |
| 8 | Smoke-сервис профиля `validation` подтверждает готовность выпуска |
| 9 | Контейнеры, сеть и тома корректно удаляются |
| 10 | MLflow вне Compose: серия экспериментов, доступность UI, регистрация модели, корректное завершение процесса |

## 3. Часть A. Контур Docker Compose

### 3.1. Подготовка и проверка конфигурации

```bash
cp .env.example .env
docker compose config
```

Результат: код возврата `0`, вывод в stderr отсутствует. Состав сервисов подтверждён командой `docker compose --profile monitoring --profile validation config --services`:

```
api
prometheus
grafana
smoke
```

### 3.2. Сборка образа

```bash
docker compose build api
```

Результат: код возврата `0`, длительность **95 с**. Итоговый образ `mlops-course-api:stable`, размер **713 MB**. Сборка многостадийная: на стадии `builder` устанавливаются зависимости, формируются данные и обучается модель; в `runtime` копируются зависимости, код, контракт и артефакт модели.

Размеры сторонних образов после загрузки: `prom/prometheus:v3.11.2` — 578 MB, `grafana/grafana:13.0.3` — 1.47 GB.

### 3.3. Запуск профиля monitoring

```bash
docker compose --profile monitoring up -d
```

Результат: код возврата `0`, длительность **68 с** с учётом загрузки образов Prometheus и Grafana. Compose дождался состояния healthy у API до запуска зависимых сервисов:

```
 Container mlops-course-api-1 Waiting
 Container mlops-course-api-1 Healthy
 Container mlops-course-prometheus-1 Started
 Container mlops-course-grafana-1 Started
```

Состояние контейнеров:

| Контейнер | Сервис | Статус | Порты |
|---|---|---|---|
| `mlops-course-api-1` | api | Up (healthy) | `0.0.0.0:8000->8000/tcp` |
| `mlops-course-prometheus-1` | prometheus | Up | `0.0.0.0:9090->9090/tcp` |
| `mlops-course-grafana-1` | grafana | Up | `0.0.0.0:3000->3000/tcp` |

Пользователь внутри контейнера API проверен командой `docker compose exec -T api id`:

```
uid=999(app) gid=999(app) groups=999(app)
```

Сервис работает от непривилегированного пользователя, как требует задание ЛР6.

### 3.4. Endpoints API

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/docs
curl http://127.0.0.1:8000/metrics
```

| Endpoint | HTTP | Фактический ответ |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","service_version":"1.0.0","model_version":"baseline-v1","release_channel":"stable","model_exists":true}` (0.004 с) |
| `GET /ready` | 200 | `{"status":"ready","service_version":"1.0.0","model_version":"baseline-v1"}` (0.004 с) |
| `GET /docs` | 200 | страница OpenAPI-документации |
| `GET /metrics` | 200 | `text/plain; version=1.0.0; charset=utf-8`, 10 060 байт |

### 3.5. Тестовый /predict

Валидный запрос сформирован из первой строки `resources/datasets/generated/test.csv` — 12 признаков `feature_00`…`feature_11`, фактическая метка `target = 1`:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [-1.3607, -0.2155, 0.5731, -5.2291, -2.4077, 4.1614, -0.424, -4.734, -5.0861, 1.7011, -4.2231, 2.9157]}'
```

Ответ: HTTP **200**, `{"prediction":1,"probability":0.9919494180444017}`, время 0.016 с. Предсказание совпало с фактической меткой.

Негативные сценарии:

| Запрос | HTTP | Фактический ответ |
|---|---:|---|
| 11 признаков вместо 12 | **422** | `type: too_short`, `msg: "List should have at least 12 items after validation, not 11"` |
| нечисловое значение признака | **422** | `type: float_parsing`, `msg: "Input should be a valid number, unable to parse string as a number"` |

Валидация схемы возвращает 4xx, а не 5xx: разделение клиентских и серверных ошибок, проверяемое в ЛР2 и ЛР8, работает.

### 3.6. Метрики

Семейства метрик, фактически присутствующие в `/metrics`:

```
mlops_http_requests_total
mlops_http_request_duration_seconds
mlops_predictions_total
mlops_prediction_probability
mlops_model_ready
mlops_service_build_info
```

Значения на момент снятия:

```
mlops_http_requests_total{endpoint="/ready",method="GET",status="200"}    15.0
mlops_http_requests_total{endpoint="/health",method="GET",status="200"}    1.0
mlops_http_requests_total{endpoint="/docs",method="GET",status="200"}      1.0
mlops_http_requests_total{endpoint="/predict",method="POST",status="200"}  1.0
mlops_http_requests_total{endpoint="/predict",method="POST",status="422"}  2.0
mlops_predictions_total{prediction="1"}                                    1.0
mlops_model_ready                                                          1.0
```

Значение 15 у `/ready` — обращения healthcheck контейнера с интервалом 5 с. Label `endpoint` принимает только известные значения, высокой кардинальности не возникает.

### 3.7. Prometheus

```bash
curl http://127.0.0.1:9090/-/healthy
curl "http://127.0.0.1:9090/api/v1/targets?state=active"
curl "http://127.0.0.1:9090/api/v1/rules"
curl "http://127.0.0.1:9090/api/v1/query?query=mlops_model_ready"
```

| Проверка | Результат |
|---|---|
| `/-/healthy` | HTTP 200, `Prometheus Server is Healthy.` |
| Активный target | `job=mlops-course-api`, `scrapeUrl=http://api:8000/metrics`, `health=up`, `lastError=''` |
| Загруженные правила | группа `mlops-course`: `MLServiceNotReady`, `MLServiceHighErrorRate`, `MLServiceHighP95Latency` — все `state: inactive`, `health: ok` |
| Запрос данных | `mlops_model_ready{job="mlops-course-api", instance="api:8000"} = 1` |

Состояние `inactive` у всех трёх правил ожидаемо: сервис исправен, доля 5xx нулевая, задержки в пределах порога.

### 3.8. Grafana

```bash
curl http://127.0.0.1:3000/api/health
curl -u admin:<пароль из .env> http://127.0.0.1:3000/api/datasources
curl -u admin:<пароль из .env> "http://127.0.0.1:3000/api/search?type=dash-db"
```

| Проверка | Результат |
|---|---|
| `/api/health` | HTTP 200, `{"database":"ok","version":"13.0.3"}` |
| Источник данных | `Prometheus`, тип `prometheus`, URL `http://prometheus:9090`, установлен по умолчанию |
| Дашборд | `MLOps Course Service`, uid `mlops-course-service`, папка `MLOps Course` |

Источник данных и дашборд подключены автоматическим провижинингом, ручная настройка не потребовалась. Пароль администратора брался из локального `.env`, созданного из [`.env.example`](../../resources/starter-project/project-baseline/.env.example); в документ он не выносится.

### 3.9. Smoke-сервис профиля validation

```bash
docker compose --profile validation run --rm smoke
```

Результат: код возврата `0`. Сервис дождался состояния healthy у API и вывел:

```
SMOKE TEST PASSED
{
  "health":     {"status": "ok", "service_version": "1.0.0", "model_version": "baseline-v1",
                 "release_channel": "stable", "model_exists": true},
  "ready":      {"status": "ready", "service_version": "1.0.0", "model_version": "baseline-v1"},
  "prediction": {"prediction": 1, "probability": 0.6300553635717617}
}
```

### 3.10. Остановка

```bash
docker compose --profile monitoring down -v
```

Результат: код возврата `0`. Удалены три контейнера, сеть `mlops-course_mlops-course` и оба тома — `mlops-course_prometheus-data` и `mlops-course_grafana-data`. Контрольная команда `docker compose ps -a` вернула пустой список.

## 4. Часть B. MLflow вне Docker Compose

Сервис MLflow в `compose.yaml` не предусмотрен: по материалам курса MLflow запускается локально с backend store в SQLite. Схема запуска не изменялась, сервис в Compose не добавлялся.

### 4.1. Подготовка

```bash
python -m pip install -e "resources/starter-project/project-baseline[all]"
python scripts/generate_data.py --output-dir data --random-state 42
```

Установка расширения `[all]` заняла **230 с** и дала MLflow 3.14.0 и DVC 3.67.1. Генератор данных вернул:

```json
{"status": "ok", "output_dir": "data",
 "files": ["train.csv", "test.csv", "production_normal.csv", "updated.csv",
           "production_drift.csv", "incident_degraded.csv", "incident_bad_schema.csv"]}
```

### 4.2. Серия экспериментов

```bash
python scripts/run_experiments.py
```

Результат: код возврата `0`, длительность **12 с**. Создано хранилище `mlflow.db` (790 528 байт), эксперимент `mlops-course-experiments`, три запуска:

| run_id | C | test_f1 | accuracy | Статус |
|---|---:|---:|---:|---|
| `7620ed7fa073` | 0.1 | 0.7715 | 0.8063 | FINISHED |
| `aa96a855c3b7` | 1.0 | 0.7764 | 0.8104 | FINISHED |
| `d463c8d66713` | 10.0 | 0.7764 | 0.8104 | FINISHED |

Все три запуска прошли quality gate `f1 >= 0.70`. Лучшим выбран `aa96a855c3b7` с `C = 1.0`.

**Регистрация модели фактически реализована.** Скрипт вывел `Successfully registered model 'mlops-course-classifier'` и `Created version '1'`. Версии присвоен alias `champion`, доступный по URI `models:/mlops-course-classifier@champion`; выполнена контрольная проверка предсказания champion-версии (`champion_smoke_prediction: 1`).

Версия модели помечена тегами прослеживаемости, полученными автоматически:

```
git_sha         d6918b97e6a5b876874001029d7fedfcbd71d496
train_sha256    57ac4da41963f889cb250fefefd67e2fc01fd3387bc3515233b5a4846dcbab65
test_sha256     46ee8430d3f3cdc8c039cceca3d8295ea0769eb83da83b8ebc8ec3d5ade1bf95
contract_sha256 d5fb1b55cef5fdc963b5cc23e93a0d872aaecaab83afef3ca53d6f370717184e
quality_gate_f1 0.7
```

### 4.3. MLflow UI

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

| Проверка | Результат |
|---|---|
| `GET /health` | HTTP 200, `OK` |
| `GET /` | HTTP 200, `text/html; charset=utf-8` |
| `GET /api/2.0/mlflow/experiments/search` | HTTP 200 |
| Эксперимент | `mlops-course-experiments` найден |
| Количество runs | **3**, все в статусе `FINISHED` |
| Зарегистрированные модели | `mlops-course-classifier` |
| Версии модели | 1 версия, статус `READY` |
| Alias | `champion` → версия `1` |

### 4.4. Завершение процесса

Процесс, слушавший порт `5000`, определён через `netstat -ano` и завершён вместе с дочерними процессами. Контрольная проверка подтвердила, что порт `5000` освобождён.

## 5. Сводка

| Шаг сценария | Результат |
|---|---|
| Проверка конфигурации Compose | пройден |
| Сборка образа API | пройден, 95 с |
| Запуск профиля monitoring | пройден, 68 с, API healthy |
| `/health`, `/ready`, `/docs`, `/metrics` | пройден, все HTTP 200 |
| `/predict` валидный и невалидный | пройден, 200 и 422 |
| Prometheus: target, правила, запрос данных | пройден, target `up` |
| Grafana: health, источник, дашборд | пройден, провижининг работает |
| Smoke-сервис профиля validation | пройден, `SMOKE TEST PASSED` |
| Остановка и удаление томов | пройден |
| MLflow вне Compose | пройден, 3 runs, модель зарегистрирована |

Все десять шагов выполнены успешно. Ошибок, потребовавших исправления кода, конфигурации или эталонного проекта, не обнаружено. Изменения в репозиторий по результатам прогона не вносились.

## 6. Ограничения и наблюдения

1. **MLflow не входит в контур Compose.** Проверка выполнена локально, как предусмотрено материалами курса. Доступность MLflow на учебной машине не гарантируется запуском профиля `monitoring` — это следует учитывать при планировании занятия по модулю 2.
2. **Сценарии drift и инцидента в прогон не входили.** Генератор трафика, drift-анализ и расследование инцидента относятся к ЛР8 и ЛР9 и проверяются отдельно.
3. **Обновление и откат выпуска не проверялись.** `release_manager.py` относится к ЛР7 и требует собственного сценария с кандидатом и стабильной версией.
4. **Правила Prometheus остались в состоянии `inactive`.** Это ожидаемо для исправного сервиса: срабатывание сигналов проверяется только на сценариях отказа из ЛР8.
5. **Время сборки зависит от кэша.** Указанные 95 с получены при уже загруженном базовом образе `python:3.11-slim`. Первый запуск на чистой машине занимает больше и требует доступа в сеть.
6. **Файлы `resources/datasets/generated/*.csv` содержат UTF-8 BOM.** На работу проекта это не влияет: `pandas.read_csv` и `load_dataset` читают их корректно, что проверено отдельно. Учитывать нужно только при разборе этих файлов сторонними средствами — например, модулем `csv` стандартной библиотеки требуется кодировка `utf-8-sig`.
7. **Прогон выполнен на одной конфигурации** — Windows с Docker Desktop и Linux-движком, 16 CPU, 15.18 GiB. На машинах с меньшим объёмом памяти поведение профиля `monitoring` может отличаться; ориентиры приведены в [troubleshooting](../teachers/troubleshooting.md).

## 7. Повторное выполнение

Последовательность для проверки стенда перед занятием. Команды 2–9 выполняются из каталога `resources/starter-project/project-baseline`.

```bash
docker version && docker compose version && docker info
cp .env.example .env
docker compose config
docker compose build api
docker compose --profile monitoring up -d
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
docker compose --profile validation run --rm smoke
docker compose --profile monitoring down -v
```

Проверка MLflow выполняется отдельно:

```bash
python scripts/generate_data.py --output-dir data --random-state 42
python scripts/run_experiments.py
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

После проверки процесс MLflow завершается, а локальные `data/`, `artifacts/`, `mlflow.db` и `.env` удаляются согласно порядку очистки из [troubleshooting](../teachers/troubleshooting.md). Все перечисленные файлы исключены `.gitignore` проекта и в репозиторий не попадают.
