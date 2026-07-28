"""Генератор учебного трафика к API.

Студенческий каркас. Реализация выполняется в ЛР8.

Скрипт формирует базовую картину метрик на штатных данных, а затем
позволяет воспроизвести аномальный поток. Параметр `--invalid-every`
задаёт долю намеренно некорректных запросов: они должны увеличивать долю
ответов 4xx, а не 5xx.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def send_traffic(*args, **kwargs) -> dict:
    """Отправить последовательность запросов и вернуть сводку по кодам ответов."""
    # TODO (ЛР8): прочитать строки данных, отправить запросы и собрать статистику.
    raise NotImplementedError("ЛР8: реализуйте генерацию трафика")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate educational traffic for the ML API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--data", type=Path, default=Path("data/production_normal.csv"))
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.02)
    parser.add_argument("--invalid-every", type=int, default=0)
    parser.parse_args()
    raise NotImplementedError("ЛР8: реализуйте запуск генератора трафика")


if __name__ == "__main__":
    main()
