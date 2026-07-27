from __future__ import annotations

import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ModuleNotFoundError:
    print('Не установлен PyYAML. Выполните: python -m pip install -e "resources/starter-project/project-baseline[dev]"')
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "resources" / "starter-project" / "project-baseline"
REQUIRED = [
    "README.md", "LICENSE.md", "CONTRIBUTING.md", "repository-tree.txt",
    "NOTICE.md", "THIRD_PARTY_NOTICES.md", "LICENSES/CC-BY-4.0.txt", "LICENSES/MIT.txt",
    ".student-exclude", "tools/check_student_delivery.py",
    "docs/README.md", "docs/rpd.md", "docs/measurement-model.md", "docs/quality-checklist.md",
    "docs/cross-validation-response.md",
    "docs/source/RPD-MLOps.docx", "docs/source/FOS-MLOps.docx",
    "data/README.md", "data/krm-v3.0.xlsx", "data/competency-catalog.csv", "data/role-competency-matrix.csv",
    "Project/README.md", "Project/submission-checklist.md", "Project/ai-use-declaration-template.md", "Project/traceability-template.md",
    "Exam/README.md", "Exam/individual-defense-protocol.md", "Exam/question-bank.md", "Exam/live-change-bank.md", "Exam/assessment-sheet.md", "Exam/scoring.json",
    "methodical-guidelines/README.md", "resources/README.md", "resources/llm-prompts/README.md",
    "resources/test-banks/README.md", "resources/test-banks/answer-key.md",
    "resources/datasets/generate_data.py", "resources/datasets/data_contract.json",
    "resources/starter-project/project-baseline/README.md", "resources/starter-project/project-baseline/pyproject.toml",
    "resources/starter-project/project-baseline/dvc.yaml", "resources/starter-project/project-baseline/dvc.lock", "resources/starter-project/project-baseline/params.yaml",
    "resources/starter-project/project-baseline/Dockerfile", "resources/starter-project/project-baseline/compose.yaml", "resources/starter-project/project-baseline/.env.example",
    "resources/starter-project/project-baseline/scripts/run_experiments.py", "resources/starter-project/project-baseline/scripts/smoke_test.py",
    "resources/starter-project/project-baseline/scripts/release_manager.py", "resources/starter-project/project-baseline/scripts/generate_traffic.py",
    "resources/starter-project/project-baseline/scripts/analyze_drift.py", "resources/starter-project/project-baseline/scripts/investigate_incident.py",
    "resources/starter-project/project-baseline/monitoring/prometheus/prometheus.yml", "resources/starter-project/project-baseline/monitoring/prometheus/rules.yml",
    "resources/starter-project/project-baseline/monitoring/grafana/dashboards/mlops-course.json", "resources/starter-project/project-baseline/monitoring/postmortem-template.md",
    "team/README.md",
]
for n in range(1, 10):
    REQUIRED.append(f"resources/test-banks/test-{n:02d}.md")
for module, count in [("M1-engineering-testing",3),("M2-reproducibility-experiments",2),("M3-deployment",2),("M4-monitoring-incidents",2)]:
    for path in sorted((ROOT/module).glob("kim-*.md")):
        REQUIRED.append(str(path.relative_to(ROOT)))
    REQUIRED.append(str(next((ROOT/module).glob("rubric-*.md")).relative_to(ROOT)))

errors: list[str] = []
for relative in REQUIRED:
    if not (ROOT / relative).exists():
        errors.append(f"Отсутствует: {relative}")

for path in ROOT.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    if "[ЗАПОЛНИТЬ]" in text or "Раздел будет заполнен" in text:
        errors.append(f"Найден незавершённый шаблон: {path.relative_to(ROOT)}")

for path in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.csv")):
    text = path.read_text(encoding="utf-8-sig")
    if "AI S-1" in text:
        errors.append(f"Использовано неканоническое написание кода AI S -1: {path.relative_to(ROOT)}")

# Relative Markdown links
link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
for path in ROOT.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for raw in link_pattern.findall(text):
        target = raw.strip().split()[0].strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = unquote(target.split("#", 1)[0])
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"Ссылка выходит за пределы репозитория: {path.relative_to(ROOT)} -> {raw}")
            continue
        if not resolved.exists():
            errors.append(f"Неработающая ссылка: {path.relative_to(ROOT)} -> {raw}")

try:
    params = yaml.safe_load((BASELINE / "params.yaml").read_text(encoding="utf-8"))
    pipeline = yaml.safe_load((BASELINE / "dvc.yaml").read_text(encoding="utf-8"))
    if not {"generate_data", "train"}.issubset(pipeline.get("stages", {})):
        errors.append("DVC-пайплайн не содержит обязательные этапы generate_data и train")
    if params["train"]["C"] <= 0:
        errors.append("Параметр train.C должен быть положительным")
except (KeyError, TypeError, yaml.YAMLError) as error:
    errors.append(f"Некорректные YAML-конфигурации модуля 2: {error}")

try:
    json.loads((ROOT / "resources/datasets/data_contract.json").read_text(encoding="utf-8"))
    json.loads((BASELINE / "monitoring/grafana/dashboards/mlops-course.json").read_text(encoding="utf-8"))
    scoring = json.loads((ROOT / "Exam/scoring.json").read_text(encoding="utf-8"))
    criteria_total = sum(item["max_points"] for item in scoring["criteria"])
    if criteria_total != scoring["max_points"] or criteria_total != 22:
        errors.append(f"Некорректная сумма баллов зачёта: критерии={criteria_total}, max_points={scoring.get('max_points')}")
except (json.JSONDecodeError, KeyError, TypeError) as error:
    errors.append(f"Некорректный JSON: {error}")

try:
    compose = yaml.safe_load((BASELINE / "compose.yaml").read_text(encoding="utf-8"))
    services = compose.get("services", {})
    required_services = {"api", "smoke", "prometheus", "grafana"}
    if not required_services.issubset(services):
        errors.append(f"Compose не содержит сервисы: {sorted(required_services - set(services))}")
    elif services["smoke"].get("depends_on", {}).get("api", {}).get("condition") != "service_healthy":
        errors.append("Smoke-сервис должен ожидать service_healthy для API")
    if services.get("prometheus", {}).get("image") != "prom/prometheus:v3.11.2":
        errors.append("Версия Prometheus должна быть зафиксирована")
    if services.get("grafana", {}).get("image") != "grafana/grafana:13.0.3":
        errors.append("Версия Grafana должна быть зафиксирована")
except yaml.YAMLError as error:
    errors.append(f"Некорректная Compose-конфигурация: {error}")

for yaml_path in [
    BASELINE / "monitoring/prometheus/prometheus.yml", BASELINE / "monitoring/prometheus/rules.yml",
    BASELINE / "monitoring/grafana/provisioning/datasources/prometheus.yml", BASELINE / "monitoring/grafana/provisioning/dashboards/dashboards.yml",
]:
    try:
        yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        errors.append(f"Некорректный YAML {yaml_path.relative_to(ROOT)}: {error}")

for script_name in ["run_experiments.py", "smoke_test.py", "release_manager.py", "generate_traffic.py", "analyze_drift.py", "investigate_incident.py"]:
    try:
        py_compile.compile(str(BASELINE / "scripts" / script_name), doraise=True)
    except py_compile.PyCompileError as error:
        errors.append(f"Синтаксическая ошибка в {script_name}: {error}")

try:
    py_compile.compile(str(ROOT / "tools" / "check_student_delivery.py"), doraise=True)
except py_compile.PyCompileError as error:
    errors.append(f"Синтаксическая ошибка в check_student_delivery.py: {error}")

# Манифест студенческой поставки должен ссылаться только на существующие пути.
try:
    from check_student_delivery import parse_manifest

    manifest = parse_manifest(ROOT / ".student-exclude")
    for section in ("exclude", "skeleton", "require"):
        for entry in manifest[section]:
            if not (ROOT / entry.rstrip("/")).exists():
                errors.append(f"Манифест .student-exclude, секция [{section}]: путь отсутствует — {entry}")
except (ImportError, ValueError, OSError) as error:
    errors.append(f"Не удалось проверить манифест .student-exclude: {error}")

if errors:
    print("Проверка не пройдена:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

env = os.environ.copy()
src = str(BASELINE / "src")
env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
for command, label in [
    ([sys.executable, "scripts/generate_data.py", "--output-dir", "data", "--random-state", "42"], "формирование данных"),
    ([sys.executable, "-m", "mlops_course.train"], "обучение модели"),
]:
    result = subprocess.run(command, cwd=BASELINE, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Не выполнено: {label}")
        print(result.stdout); print(result.stderr)
        sys.exit(result.returncode)

result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=BASELINE, env=env, text=True, capture_output=True)
if result.returncode != 0:
    print("Тесты базового проекта не пройдены:")
    print(result.stdout); print(result.stderr)
    sys.exit(result.returncode)

print("Структурная проверка и проверка ссылок пройдены.")
print(result.stdout.strip())
print("Репозиторий прошёл базовую техническую проверку.")
