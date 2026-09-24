import ast
from pathlib import Path

ROOT = Path("src")

print("=" * 80)
print("DAY 44 — PUBLIC DOCSTRING AUDIT")
print("=" * 80)

missing = []
total_functions = 0
documented_functions = 0

for path in sorted(ROOT.rglob("*.py")):
    # Skip historical backup files
    if "backup" in path.parts or "_before_" in path.name or "_backup" in path.name:
        continue

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        print(f"\nPARSE ERROR: {path}")
        print(f"  {exc}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Public function = does not start with "_"
            if node.name.startswith("_"):
                continue

            total_functions += 1

            if ast.get_docstring(node):
                documented_functions += 1
            else:
                missing.append(
                    (
                        str(path),
                        node.lineno,
                        node.name,
                    )
                )

print()
print(f"Public functions found : {total_functions}")
print(f"With docstrings        : {documented_functions}")
print(f"Missing docstrings     : {len(missing)}")

print()
print("-" * 80)
print("MISSING PUBLIC DOCSTRINGS")
print("-" * 80)

if not missing:
    print("ALL PUBLIC FUNCTIONS HAVE DOCSTRINGS")
else:
    for path, line, name in missing:
        print(f"{path}:{line} -> {name}()")

print()
print("=" * 80)
print("DOCSTRING AUDIT COMPLETE")
print("=" * 80)
