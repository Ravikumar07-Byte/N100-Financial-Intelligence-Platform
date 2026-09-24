from pathlib import Path

p = Path("README.md")

if not p.exists():
    print("README CHECK: FAIL - README.md missing")
    raise SystemExit(1)

text = p.read_text(encoding="utf-8").lower()

checks = {
    "Project overview": (
        "financial intelligence" in text
        or "project overview" in text
    ),
    "Setup": (
        "python -m venv" in text
        or "installation" in text
        or "setup" in text
    ),
    "ETL": (
        "etl" in text
    ),
    "Dashboard": (
        "streamlit run" in text
    ),
    "API": (
        "uvicorn" in text
        and "fastapi" in text
    ),
    "Tests": (
        "pytest" in text
    ),
}

print("=" * 70)

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'MISSING'}")

print("=" * 70)

if all(checks.values()):
    print("README CHECK: PASS")
else:
    print("README CHECK: FAIL")
