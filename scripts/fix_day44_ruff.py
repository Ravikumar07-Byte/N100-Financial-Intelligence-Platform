from pathlib import Path
import re


ROOT = Path(".")


def replace_once(path, old, new, description):
    """Replace one exact block in a source file."""
    text = path.read_text(encoding="utf-8")

    if old not in text:
        print(f"SKIP: {path} -> {description} (pattern not found)")
        return False

    if text.count(old) > 1:
        print(
            f"SKIP: {path} -> {description} "
            f"(pattern appears {text.count(old)} times)"
        )
        return False

    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"FIXED: {path} -> {description}")
    return True


def replace_all(path, old, new, description):
    """Replace all exact occurrences in a source file."""
    text = path.read_text(encoding="utf-8")

    count = text.count(old)

    if count == 0:
        print(f"SKIP: {path} -> {description} (pattern not found)")
        return False

    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"FIXED: {path} -> {description} ({count} occurrence(s))")
    return True


print("=" * 80)
print("DAY 44 — RUFF SAFE CODE CLEANUP")
print("=" * 80)


# ============================================================================
# 1. SCREENER ENGINE — IMPORT ORDER + CLASS CONSTANTS
# ============================================================================

engine = ROOT / "src/screener/engine.py"

if engine.exists():
    replace_once(
        engine,
        """from pathlib import Path
import sqlite3

import pandas as pd
import yaml
""",
        """import sqlite3
from pathlib import Path
from typing import ClassVar

import pandas as pd
import yaml
""",
        "organize imports and add ClassVar",
    )

    replace_once(
        engine,
        """    FILTER_COLUMN_MAP = {
""",
        """    FILTER_COLUMN_MAP: ClassVar[dict[str, str]] = {
""",
        "annotate FILTER_COLUMN_MAP with ClassVar",
    )

    replace_once(
        engine,
        """    SPECIAL_FILTERS = {
""",
        """    SPECIAL_FILTERS: ClassVar[set[str]] = {
""",
        "annotate SPECIAL_FILTERS with ClassVar",
    )


# ============================================================================
# 2. HISTORICAL SCREENER FILES
#
# We intentionally do NOT modify these.
# They are historical snapshots and should be excluded from Ruff.
# ============================================================================

print()
print("Historical screener snapshots intentionally left unchanged.")


# ============================================================================
# 3. ANALYTICS — UNUSED company_id
# ============================================================================

peer_comparison = ROOT / "src/analytics/peer_comparison.py"

if peer_comparison.exists():
    text = peer_comparison.read_text(encoding="utf-8")

    # Only remove an assignment if the variable is genuinely unused
    # in the local function. We do this conservatively.
    lines = text.splitlines(keepends=True)

    target_line = 1098

    if len(lines) >= target_line:
        line = lines[target_line - 1]

        if "company_id =" in line:
            print(
                "CHECK: src/analytics/peer_comparison.py:1098 "
                "contains company_id assignment."
            )
            print(
                "       This assignment is NOT automatically deleted because "
                "the RHS may have side effects."
            )


# ============================================================================
# 4. ANALYTICS — UNUSED files
# ============================================================================

radar = ROOT / "src/analytics/radar.py"

if radar.exists():
    lines = radar.read_text(encoding="utf-8").splitlines(keepends=True)

    target_line = 1263

    if len(lines) >= target_line:
        line = lines[target_line - 1]

        if re.match(r"^\s*files\s*=", line):
            print(
                "CHECK: src/analytics/radar.py:1263 "
                "contains unused 'files' assignment."
            )
            print(
                "       This assignment is NOT automatically deleted because "
                "the RHS may have side effects."
            )


# ============================================================================
# 5. NLP PROS/CONS GENERATOR
# ============================================================================

pros_cons = ROOT / "src/nlp/pros_cons_generator.py"

if pros_cons.exists():

    replace_once(
        pros_cons,
        """from pathlib import Path
import sqlite3
import math
import re

import numpy as np
import pandas as pd
""",
        """import math
import re
import sqlite3
from pathlib import Path

import pandas as pd
""",
        "organize imports and remove unused numpy",
    )

    replace_once(
        pros_cons,
        """confidence = max(0, min(int(round(confidence)), 100))
""",
        """confidence = max(0, min(round(confidence), 100))
""",
        "remove redundant int cast from confidence",
    )

    # We only remove the assignment if the exact multiline expression is found.
    replace_once(
        pros_cons,
        """    roe = latest_value(
        ratios,
        company_id,
        "return_on_equity_pct",
    )
""",
        "",
        "remove unused roe calculation",
    )


# ============================================================================
# 6. API SCREENER — NaN CHECK
# ============================================================================

api_screener = ROOT / "src/api/routers/screener.py"

if api_screener.exists():
    text = api_screener.read_text(encoding="utf-8")

    # Ensure pandas is imported if it isn't already.
    if "import pandas as pd" not in text:
        if "import pandas" not in text:
            marker = "from fastapi"
            if marker in text:
                text = text.replace(
                    marker,
                    "import pandas as pd\n\n" + marker,
                    1,
                )
                api_screener.write_text(text, encoding="utf-8")
                print(
                    "FIXED: src/api/routers/screener.py "
                    "-> added pandas import"
                )

    replace_all(
        api_screener,
        "value != value",
        "pd.isna(value)",
        "replace self-comparison NaN check",
    )


# ============================================================================
# 7. API CLIENT — TYPE ERRORS
# ============================================================================

api_client = ROOT / "src/dashboard/utils/api_client.py"

if api_client.exists():
    text = api_client.read_text(encoding="utf-8")

    # These are handled manually below if the exact messages are visible.
    print()
    print(
        "CHECK: api_client.py TRY004 issues at lines 101 and 113 "
        "should use TypeError for invalid argument types."
    )


# ============================================================================
# 8. DATETIME TEST
# ============================================================================

normalise_test = ROOT / "tests/etl/test_normalise.py"

if normalise_test.exists():
    text = normalise_test.read_text(encoding="utf-8")

    if "from datetime import datetime" in text:
        text = text.replace(
            "from datetime import datetime",
            "from datetime import datetime, timezone",
            1,
        )
    elif "from datetime import" not in text:
        text = "from datetime import datetime, timezone\n" + text

    replace_once(
        normalise_test,
        """(datetime(2024, 9, 30), "2024-09"),
""",
        """(datetime(2024, 9, 30, tzinfo=timezone.utc), "2024-09"),
""",
        "make test datetime timezone-aware",
    )

    normalise_test.write_text(text, encoding="utf-8")


# ============================================================================
# 9. API ROUTERS __init__.py
# ============================================================================

routers_init = ROOT / "src/api/routers/__init__.py"

if routers_init.exists():
    text = routers_init.read_text(encoding="utf-8")

    router_names = [
        "companies",
        "documents",
        "health",
        "market_cap",
        "peers",
        "portfolio",
        "screener",
        "sectors",
        "valuation",
    ]

    all_block = "__all__ = [\n" + "".join(
        f'    "{name}",\n' for name in router_names
    ) + "]\n"

    if "__all__" not in text:
        text = text.rstrip() + "\n\n\n" + all_block
        routers_init.write_text(text, encoding="utf-8")
        print(
            "FIXED: src/api/routers/__init__.py "
            "-> added __all__"
        )
    else:
        print(
            "SKIP: src/api/routers/__init__.py "
            "-> __all__ already exists"
        )


# ============================================================================
# 10. SUMMARY
# ============================================================================

print()
print("=" * 80)
print("RUFF SAFE CODE CLEANUP COMPLETE")
print("=" * 80)
print()
print("Historical backup files were NOT modified.")
print()
print("Next steps:")
print("1. black src\\ tests\\")
print("2. black --check src\\ tests\\")
print("3. ruff check src tests --output-format=concise")
print("4. pytest -q")
print("=" * 80)
