# Инструменты проверки

`validate_repository.py` проверяет обязательные документы и КИМ, отсутствие шаблонных маркеров, относительные Markdown-ссылки, JSON/YAML, синтаксис учебных скриптов и состав тестового банка. Затем он генерирует данные, обучает модель и запускает тесты базового проекта.

## Подготовка окружения

Из корня репозитория:

```bash
python -m pip install -e "resources/starter-project/project-baseline[dev]"
python tools/validate_repository.py
```

Валидатор автоматически добавляет `resources/starter-project/project-baseline/src` в `PYTHONPATH`, поэтому обучение и тесты запускаются и без отдельной editable-установки самого пакета, если остальные зависимости уже доступны.

Скрипт не запускает Docker. Контейнерная сборка, Prometheus и Grafana проверяются отдельно на машине с Docker Engine/Desktop.
