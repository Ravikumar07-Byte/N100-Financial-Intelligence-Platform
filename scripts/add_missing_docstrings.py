import ast
from pathlib import Path

ROOT = Path("src")

SKIP_DIRS = {
    "backup_day25",
    "backup_day27",
}

def make_docstring(name):
    """Create a simple one-line docstring for a public function."""
    readable = name.replace("_", " ")
    return f"{readable.capitalize()}."

changed = 0
files_changed = 0

for path in ROOT.rglob("*.py"):
    if any(part in SKIP_DIRS for part in path.parts):
        continue

    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
    except Exception as exc:
        print(f"SKIPPED: {path} -> {exc}")
        continue

    lines = source.splitlines(keepends=True)
    insertions = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if node.name.startswith("_"):
            continue

        if ast.get_docstring(node) is not None:
            continue

        if not node.body:
            continue

        first_stmt = node.body[0]

        # Insert after the function declaration and any decorators.
        # node.lineno is the def line.
        def_line_index = node.lineno - 1

        # Handle multiline function signatures by finding the colon
        # belonging to this function definition.
        depth = 0
        end_line_index = def_line_index

        for i in range(def_line_index, len(lines)):
            text = lines[i]

            depth += text.count("(")
            depth -= text.count(")")

            if ":" in text and depth == 0:
                end_line_index = i
                break

        indent = " " * (node.col_offset + 4)
        docstring = f'{indent}"""{make_docstring(node.name)}"""\n'

        insertions.append((end_line_index + 1, docstring, path))

    if not insertions:
        continue

    for line_number, text, _ in sorted(
        insertions,
        key=lambda x: x[0],
        reverse=True,
    ):
        lines.insert(line_number, text)
        changed += 1

    path.write_text("".join(lines), encoding="utf-8")
    files_changed += 1
    print(f"UPDATED: {path}")

print()
print("=" * 70)
print("DAY 44 — PUBLIC FUNCTION DOCSTRING UPDATE")
print("=" * 70)
print(f"Functions documented : {changed}")
print(f"Files changed        : {files_changed}")
print("=" * 70)
