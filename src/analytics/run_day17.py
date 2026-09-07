"""
N100 Financial Intelligence Platform
Sprint 3 - Day 17

Composite Quality Score and Excel Export Runner.

Calculates the composite quality score for the complete
92-company universe and exports all six screener presets.
"""

from pathlib import Path
import sys
import sqlite3

import pandas as pd


# =====================================================================
# PROJECT ROOT
# =====================================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =====================================================================
# PROJECT IMPORTS
# =====================================================================

from src.screener.engine import ScreenerEngine

from src.analytics.composite_score import (
    CompositeScoreCalculator,
    generate_screener_export,
)


# =====================================================================
# MAIN
# =====================================================================

def main():

    print("=" * 70)
    print("N100 FINANCIAL INTELLIGENCE PLATFORM")
    print("Sprint 3 - Day 17")
    print("Composite Quality Score & Excel Export")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Initialize engine
    # ---------------------------------------------------------------

    engine = ScreenerEngine()

    # ---------------------------------------------------------------
    # Load complete universe
    # ---------------------------------------------------------------

    universe = engine.load_universe()

    print()
    print("Universe")
    print("-" * 70)

    print(
        "Companies:",
        len(universe),
    )

    print(
        "Unique companies:",
        universe["company_id"].nunique(),
    )

    # ---------------------------------------------------------------
    # Validate universe
    # ---------------------------------------------------------------

    if len(universe) != 92:

        raise ValueError(
            "Expected 92 companies, "
            f"but found {len(universe)}."
        )

    if (
        universe["company_id"].nunique()
        != 92
    ):

        raise ValueError(
            "Expected 92 unique company IDs."
        )

    # ---------------------------------------------------------------
    # Load historical FCF data
    # ---------------------------------------------------------------

    print()
    print("Historical FCF Data")
    print("-" * 70)

    with sqlite3.connect(
        engine.db_path
    ) as conn:

        fcf_history = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                free_cash_flow_cr
            FROM financial_ratios
            ORDER BY
                company_id,
                year
            """,
            conn,
        )

    print(
        "Historical rows:",
        len(fcf_history),
    )

    print(
        "Companies with FCF history:",
        fcf_history[
            "company_id"
        ].nunique(),
    )

    # ---------------------------------------------------------------
    # Composite score
    # ---------------------------------------------------------------

    calculator = CompositeScoreCalculator()

    scored_universe = (
        calculator.calculate(
            universe,
            fcf_history,
        )
    )

    print()
    print("Composite Score")
    print("-" * 70)

    score_series = pd.to_numeric(
        scored_universe[
            "composite_quality_score"
        ],
        errors="coerce",
    )

    print(
        "Minimum:",
        score_series.min(),
    )

    print(
        "Maximum:",
        score_series.max(),
    )

    print(
        "Average:",
        round(
            score_series.mean(),
            2,
        ),
    )

    print(
        "Missing scores:",
        score_series.isna().sum(),
    )

    # ---------------------------------------------------------------
    # Validate composite score
    # ---------------------------------------------------------------

    if score_series.notna().any():

        if (
            score_series.min() < 0
            or score_series.max() > 100
        ):

            raise ValueError(
                "Composite score is outside "
                "the required 0-100 range."
            )

    # ---------------------------------------------------------------
    # Run all six screener presets
    # ---------------------------------------------------------------

    screener_results = {}
    screener_configs = {}

    print()
    print("Screener Results")
    print("-" * 70)

    for screener_name in (
        engine.get_screener_names()
    ):

        # IMPORTANT:
        # Do NOT calculate the composite score again.
        #
        # scored_universe already contains:
        # - fcf_cagr_5yr
        # - cfo_pat_ratio
        # - metric scores
        # - component scores
        # - composite_quality_score

        result = engine.apply_filters(
            scored_universe,
            screener_name,
        )

        result = result.sort_values(
            "composite_quality_score",
            ascending=False,
            na_position="last",
        ).reset_index(
            drop=True
        )

        screener_results[
            screener_name
        ] = result

        config = (
            engine.get_screener_config(
                screener_name
            )
        )

        screener_configs[
            screener_name
        ] = config

        display_name = config[
            "name"
        ]

        print(
            f"{display_name}: "
            f"{len(result)} companies"
        )

    # ---------------------------------------------------------------
    # Validate six presets
    # ---------------------------------------------------------------

    expected_screeners = 6

    if len(screener_results) != expected_screeners:

        raise ValueError(
            "Expected "
            f"{expected_screeners} screener presets, "
            f"found {len(screener_results)}."
        )

    # ---------------------------------------------------------------
    # Excel export
    # ---------------------------------------------------------------

    print()
    print("Excel Export")
    print("-" * 70)

    output_file = (
        generate_screener_export(
            screener_results,
            screener_configs,
        )
    )

    print(
        "Created:",
        output_file,
    )

    print(
        "Sheets:",
        len(screener_results),
    )

    # ---------------------------------------------------------------
    # Validate output file
    # ---------------------------------------------------------------

    if not output_file.exists():

        raise FileNotFoundError(
            "Excel output file was not created."
        )

    print(
        "File size:",
        output_file.stat().st_size,
        "bytes",
    )

    print()
    print("=" * 70)
    print("DAY 17 COMPLETED SUCCESSFULLY")
    print("=" * 70)


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    main()