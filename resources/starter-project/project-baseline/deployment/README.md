# Развёртывание и учебный выпуск

Документ описывает целевое поведение, которое требуется реализовать в ЛР6 и ЛР7. Приведённые команды становятся работоспособными по мере выполнения этих работ.

## Архитектура

```text
                         Docker Compose project
┌──────────────┐       ┌──────────────────────────────────┐
│ HTTP client  │ ----> │ api:8000                         │
└──────────────┘       │ FastAPI -> model.joblib          │
                       │ /health /ready /predict           │
                       └───────────────┬──────────────────┘
                                       │ service_healthy
                                       v
                       ┌──────────────────────────────────┐
                       │ smoke (profile: validation)      │
                       │ one-shot release checks          │
                       └──────────────────────────────────┘
```

Образ является самодостаточным: на стадии сборки генерируются воспроизводимые данные и обучается небольшая модель. В runtime-слой копируются установленные зависимости, код, контракт и модельный артефакт.

## Базовые команды

```bash
cp .env.example .env
docker compose config
docker compose build api
docker compose up -d api
python scripts/smoke_test.py --base-url http://127.0.0.1:8000
docker compose --profile validation run --rm smoke
docker compose down
```

## Выпуск стабильной версии

```bash
python scripts/release_manager.py build   --tag stable   --service-version 1.0.0   --model-version baseline-v1   --model-c 1.0

python scripts/release_manager.py deploy   --tag stable   --expected-version 1.0.0
```

## Кандидат и откат

```bash
python scripts/release_manager.py build   --tag candidate   --service-version 1.1.0   --model-version baseline-v2   --model-c 0.5

# Учебный отказ: менеджер должен вернуть предыдущую версию.
python scripts/release_manager.py deploy   --tag candidate   --expected-version 1.1.0   --simulate-failure

# Успешное обновление.
python scripts/release_manager.py deploy   --tag candidate   --expected-version 1.1.0
```

Команда с `--simulate-failure` ожидаемо завершается ненулевым кодом после успешного восстановления стабильной версии. Это позволяет использовать её как демонстрацию блокировки релиза.

## Критерии отката

Обязательный откат выполняется, если:

1. контейнер не достигает ready-состояния за установленный срок;
2. smoke-тест не проходит;
3. версия сервиса не совпадает с ожидаемой;
4. `/predict` нарушает контракт;
5. предыдущая стабильная версия может быть восстановлена и повторно проверена.

В промышленной системе к этим условиям добавляются метрики ошибок, задержек, качества модели и бизнес-ограничения. В учебной работе достаточно детерминированного локального сценария.

## Файлы состояния

- `.env` — текущая локальная конфигурация выпуска, не коммитится;
- `release-history.jsonl` — локальный журнал событий, не коммитится;
- `.env.example` — безопасный шаблон без секретов, коммитится.

## Безопасность

- не помещайте API-ключи и пароли в Dockerfile, образ, README и Git;
- не выводите секреты в журнал релиза;
- фиксируйте зависимости и теги образов;
- перед публикацией выполняйте поиск случайно добавленных секретов;
- используйте непривилегированного пользователя внутри контейнера.
