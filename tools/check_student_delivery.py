"""Проверка состава студенческой поставки по манифесту `.student-exclude`.

Скрипт подтверждает, что в проверяемом дереве отсутствуют ключи ответов,
эталонные решения и преподавательские материалы, что обязательные учебные
материалы на месте, а файлы-каркасы действительно содержат TODO вместо
готовой реализации.

Проверка построена на конкретных путях, известных именах файлов и точных
структурных сигнатурах известных материалов. Обычные слова методических
текстов («ключ», «ответ», «решение») не приводят к срабатыванию.

Примеры запуска:

    python tools/check_student_delivery.py --root .
    python tools/check_student_delivery.py --root ../student-worktree
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MANIFEST_NAME = ".student-exclude"
SECTIONS = ("exclude", "skeleton", "require", "forbidden-names")
SKELETON_MARKER = "TODO"

# Точные структурные сигнатуры известных преподавательских материалов.
# Каждая сигнатура описывает форму записи, а не отдельное слово.
CONTENT_SIGNATURES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "ключ к коротким тестам",
        "строка таблицы ключа вида «| 1 | 1-Б, 2-В, 3-Г, 4-А |»",
        re.compile(r"^\s*\|\s*\d+\s*\|\s*\d+-[А-Г](?:\s*,\s*\d+-[А-Г]){2,}\s*\|", re.MULTILINE),
    ),
    (
        "заголовок ключа",
        "заголовок «# Ключ к коротким тестам»",
        re.compile(r"^#{1,6}\s+Ключ к коротким тестам\s*$", re.MULTILINE),
    ),
    (
        "маркер преподавательского материала",
        "строка «Материал для преподавателя. Не включать в студенческую выдачу.»",
        re.compile(r"Материал для преподавателя\.\s*Не включать в студенческую выдачу\."),
    ),
]

SCANNED_SUFFIXES = {".md", ".txt", ".json", ".csv", ".yml", ".yaml", ".py"}
SKIPPED_DIRECTORIES = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


def parse_manifest(path: Path) -> dict[str, list[str]]:
    """Прочитать манифест и вернуть содержимое секций."""
    sections: dict[str, list[str]] = {name: [] for name in SECTIONS}
    current: str | None = None
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            if current not in sections:
                raise ValueError(f"{path.name}, строка {number}: неизвестная секция [{current}]")
            continue
        if current is None:
            raise ValueError(f"{path.name}, строка {number}: запись вне секции")
        sections[current].append(line)
    return sections


def iterate_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIPPED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        yield path


def check_excluded(root: Path, entries: list[str]) -> list[str]:
    problems = []
    for entry in entries:
        target = root / entry.rstrip("/")
        if not target.exists():
            continue
        kind = "каталог" if entry.endswith("/") else "файл"
        problems.append(f"Исключённый {kind} присутствует в поставке: {entry}")
    return problems


def check_required(root: Path, entries: list[str]) -> list[str]:
    return [f"Отсутствует обязательный материал: {entry}" for entry in entries if not (root / entry).exists()]


def check_skeletons(root: Path, entries: list[str]) -> list[str]:
    problems = []
    for entry in entries:
        target = root / entry
        if not target.exists():
            problems.append(f"Отсутствует файл-каркас: {entry}")
            continue
        if SKELETON_MARKER not in target.read_text(encoding="utf-8"):
            problems.append(f"Файл-каркас не содержит маркер {SKELETON_MARKER}: {entry}")
    return problems


def check_forbidden_names(root: Path, names: list[str]) -> list[str]:
    forbidden = {name.lower() for name in names}
    problems = []
    for path in iterate_files(root):
        if path.name.lower() in forbidden:
            problems.append(f"Недопустимое имя файла в поставке: {path.relative_to(root).as_posix()}")
    return problems


def check_content_signatures(root: Path) -> list[str]:
    problems = []
    for path in iterate_files(root):
        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        if path.name == MANIFEST_NAME or path.name == Path(__file__).name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, description, pattern in CONTENT_SIGNATURES:
            if pattern.search(text):
                relative = path.relative_to(root).as_posix()
                problems.append(f"Обнаружен {label} в {relative}: {description}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка состава студенческой поставки")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="каталог проверяемой поставки (по умолчанию — корень репозитория)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=f"путь к манифесту (по умолчанию — {MANIFEST_NAME} в каталоге поставки)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Каталог не найден: {root}")
        return 2

    manifest_path = (args.manifest or root / MANIFEST_NAME).resolve()
    if not manifest_path.is_file():
        print(f"Манифест не найден: {manifest_path}")
        return 2

    try:
        sections = parse_manifest(manifest_path)
    except ValueError as error:
        print(f"Некорректный манифест: {error}")
        return 2

    problems: list[str] = []
    problems += check_excluded(root, sections["exclude"])
    problems += check_forbidden_names(root, sections["forbidden-names"])
    problems += check_content_signatures(root)
    problems += check_required(root, sections["require"])
    problems += check_skeletons(root, sections["skeleton"])

    print(f"Проверяемая поставка: {root}")
    print(f"Манифест: {manifest_path}")
    print(
        "Проверено записей: "
        f"исключений — {len(sections['exclude'])}, "
        f"каркасов — {len(sections['skeleton'])}, "
        f"обязательных материалов — {len(sections['require'])}, "
        f"запрещённых имён — {len(sections['forbidden-names'])}."
    )

    if problems:
        print("Проверка студенческой поставки не пройдена:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Студенческая поставка не содержит ключей, эталонных решений и преподавательских материалов.")
    print("Обязательные учебные материалы и файлы-каркасы на месте.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
