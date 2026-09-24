import ast
from pathlib import Path

files = list(Path("src").rglob("*.py"))
missing = []
total = 0

for path in files:
    tree = ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue

            total += 1

            if not ast.get_docstring(node):
                missing.append(
                    (str(path), node.lineno, node.name)
                )

print("=" * 70)
print(f"Public functions: {total}")
print(f"Missing docstrings: {len(missing)}")
print("=" * 70)

for path, line, name in missing:
    print(f"{path}:{line} -> {name}")

print("=" * 70)

if missing:
    print("DOCSTRING CHECK: FAIL")
else:
    print("DOCSTRING CHECK: PASS")
