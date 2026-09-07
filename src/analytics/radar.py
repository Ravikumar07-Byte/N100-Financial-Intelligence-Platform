"""
N100 Financial Intelligence Platform
Sprint 3 - Day 19

Peer Radar Charts

Implements:
- 8-axis radar/polar charts
- Company polygon
- Peer-group average dashed outline
- Peer-group percentile-based comparison
- Nifty 100 average reference for companies without peers
- PNG export to reports/radar_charts/
- Readable standard-size charts
- Uses Day 17 composite quality score calculation
- Safely skips companies without financial data
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =====================================================================
# PATHS
# =====================================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = ROOT_DIR / "nifty100.db"

OUTPUT_DIR = (
    ROOT_DIR
    / "reports"
    / "radar_charts"
)


# =====================================================================
# RADAR AXES
# =====================================================================

RADAR_METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF score",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "Composite Score",
]


# =====================================================================
# SOURCE METRIC MAPPING
# =====================================================================

PEER_METRIC_MAP = {
    "ROE": "ROE",
    "ROCE": "ROCE",
    "NPM": "Net Profit Margin",
    "D/E": "D/E",
    "PAT CAGR 5yr": "PAT CAGR 5yr",
    "Revenue CAGR 5yr": "Revenue CAGR 5yr",
}


# =====================================================================
# RADAR CALCULATOR
# =====================================================================

class RadarChartGenerator:
    """
    Generate Sprint 3 Day 19 radar charts.
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
        output_dir: Path = OUTPUT_DIR,
    ):
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # -----------------------------------------------------------------
    # Database connection
    # -----------------------------------------------------------------

    def get_connection(self):
        """
        Return SQLite database connection.
        """
        return sqlite3.connect(self.db_path)

    # -----------------------------------------------------------------
    # Load peer percentiles
    # -----------------------------------------------------------------

    def load_peer_percentiles(
        self,
    ) -> pd.DataFrame:
        """
        Load Day 18 peer percentile data.
        """

        with self.get_connection() as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    company_id,
                    peer_group_name,
                    metric,
                    value,
                    percentile_rank,
                    year
                FROM peer_percentiles
                """,
                conn,
            )

        if df.empty:
            raise ValueError(
                "peer_percentiles table is empty."
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        df["percentile_rank"] = pd.to_numeric(
            df["percentile_rank"],
            errors="coerce",
        )

        return df

    # -----------------------------------------------------------------
    # Load latest financial data
    # -----------------------------------------------------------------

    def load_company_scores(
        self,
    ) -> pd.DataFrame:
        """
        Load latest financial metrics.

        The Day 17 composite score is calculated here
        from the available financial data so that the
        radar charts use the same score methodology
        rather than relying on an older database value.

        The dataframe contains one latest financial row
        per company.
        """

        with self.get_connection() as conn:

            query = """
                WITH ranked AS (
                    SELECT
                        fr.*,

                        ROW_NUMBER() OVER (
                            PARTITION BY fr.company_id
                            ORDER BY fr.year DESC
                        ) AS rn

                    FROM financial_ratios fr
                )

                SELECT
                    r.company_id,
                    r.year,

                    r.return_on_equity_pct,
                    r.return_on_capital_employed_pct,
                    r.net_profit_margin_pct,

                    r.debt_to_equity,
                    r.interest_coverage,

                    r.free_cash_flow_cr,
                    r.cash_from_operations_cr,

                    r.pat_cagr_5yr,
                    r.revenue_cagr_5yr,

                    r.composite_quality_score

                FROM ranked r

                WHERE r.rn = 1

                ORDER BY r.company_id
            """

            df = pd.read_sql_query(
                query,
                conn,
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        numeric_columns = [
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "cash_from_operations_cr",
            "pat_cagr_5yr",
            "revenue_cagr_5yr",
            "composite_quality_score",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        return df

    # -----------------------------------------------------------------
    # Load company master
    # -----------------------------------------------------------------

    def load_companies(
        self,
    ) -> pd.DataFrame:
        """
        Load complete company master universe.
        """

        with self.get_connection() as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    id AS company_id,
                    company_name
                FROM companies
                ORDER BY id
                """,
                conn,
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        df["company_name"] = (
            df["company_name"]
            .astype(str)
        )

        return df

    # -----------------------------------------------------------------
    # Load historical FCF data
    # -----------------------------------------------------------------

    def load_fcf_history(
        self,
    ) -> pd.DataFrame:
        """
        Load historical FCF values required for
        Day 17 composite-score calculation.
        """

        with self.get_connection() as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    company_id,
                    year,
                    free_cash_flow_cr
                FROM financial_ratios
                ORDER BY company_id, year
                """,
                conn,
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce",
        )

        df["free_cash_flow_cr"] = pd.to_numeric(
            df["free_cash_flow_cr"],
            errors="coerce",
        )

        return df

    # -----------------------------------------------------------------
    # Day 17 composite score
    # -----------------------------------------------------------------

    def calculate_day17_composite_score(
        self,
        company_scores: pd.DataFrame,
        fcf_history: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate the Day 17 composite quality score.

        If the Day 17 analytics module is available,
        use it directly.

        Otherwise retain the database score as fallback.
        """

        try:

            import sys

            analytics_dir = (
                ROOT_DIR
                / "src"
                / "analytics"
            )

            if str(analytics_dir) not in sys.path:

                sys.path.insert(
                    0,
                    str(analytics_dir),
                )

            from composite_score import (
                CompositeScoreCalculator,
            )

            calculator = (
                CompositeScoreCalculator()
            )

            scored = calculator.calculate(
                company_scores.copy(),
                fcf_history.copy(),
            )

            if (
                "composite_quality_score"
                not in scored.columns
            ):
                raise ValueError(
                    "Day 17 calculator did not return "
                    "composite_quality_score."
                )

            scored[
                "composite_quality_score"
            ] = pd.to_numeric(
                scored[
                    "composite_quality_score"
                ],
                errors="coerce",
            )

            return scored

        except Exception as exc:

            print()
            print(
                "WARNING: Day 17 composite-score "
                "recalculation unavailable."
            )

            print(
                "Reason:",
                str(exc),
            )

            print(
                "Using database composite_quality_score "
                "as fallback."
            )

            return company_scores

    # -----------------------------------------------------------------
    # Calculate peer-average radar
    # -----------------------------------------------------------------

    def build_peer_radar_data(
        self,
        company_id: str,
        peer_group: str,
        peer_percentiles: pd.DataFrame,
        company_scores: pd.DataFrame,
    ):
        """
        Build company and peer-average radar values.

        Percentile metrics are represented on a
        0-100 scale.
        """

        company_peer = peer_percentiles[
            (
                peer_percentiles[
                    "company_id"
                ]
                == company_id
            )
            &
            (
                peer_percentiles[
                    "peer_group_name"
                ]
                == peer_group
            )
        ].copy()

        company_row = company_scores[
            company_scores[
                "company_id"
            ]
            == company_id
        ]

        if company_row.empty:

            return None, None

        company_row = company_row.iloc[0]

        peer_group_data = peer_percentiles[
            peer_percentiles[
                "peer_group_name"
            ]
            == peer_group
        ].copy()

        company_values = {}
        peer_average_values = {}

        # -------------------------------------------------------------
        # Percentile metrics
        # -------------------------------------------------------------

        for axis in [
            "ROE",
            "ROCE",
            "NPM",
            "D/E",
            "PAT CAGR 5yr",
            "Revenue CAGR 5yr",
        ]:

            metric_name = (
                PEER_METRIC_MAP[axis]
            )

            company_metric = (
                company_peer[
                    company_peer[
                        "metric"
                    ]
                    == metric_name
                ]
            )

            peer_metric = (
                peer_group_data[
                    peer_group_data[
                        "metric"
                    ]
                    == metric_name
                ]
            )

            if company_metric.empty:

                company_value = np.nan

            else:

                company_value = (
                    float(
                        company_metric[
                            "percentile_rank"
                        ].iloc[0]
                    )
                    * 100
                )

            if peer_metric.empty:

                peer_average = np.nan

            else:

                peer_average = (
                    peer_metric[
                        "percentile_rank"
                    ]
                    .mean()
                    * 100
                )

            company_values[
                axis
            ] = company_value

            peer_average_values[
                axis
            ] = peer_average

        # -------------------------------------------------------------
        # FCF score
        # -------------------------------------------------------------

        company_fcf = company_peer[
            company_peer[
                "metric"
            ]
            == "FCF"
        ]

        peer_fcf = peer_group_data[
            peer_group_data[
                "metric"
            ]
            == "FCF"
        ]

        if company_fcf.empty:

            company_values[
                "FCF score"
            ] = np.nan

        else:

            company_values[
                "FCF score"
            ] = (
                float(
                    company_fcf[
                        "percentile_rank"
                    ].iloc[0]
                )
                * 100
            )

        if peer_fcf.empty:

            peer_average_values[
                "FCF score"
            ] = np.nan

        else:

            peer_average_values[
                "FCF score"
            ] = (
                peer_fcf[
                    "percentile_rank"
                ].mean()
                * 100
            )

        # -------------------------------------------------------------
        # Composite Score
        # -------------------------------------------------------------

        company_composite = pd.to_numeric(
            company_row[
                "composite_quality_score"
            ],
            errors="coerce",
        )

        company_values[
            "Composite Score"
        ] = company_composite

        peer_company_ids = (
            peer_group_data[
                "company_id"
            ]
            .drop_duplicates()
        )

        peer_composite = company_scores[
            company_scores[
                "company_id"
            ].isin(
                peer_company_ids
            )
        ][
            "composite_quality_score"
        ]

        peer_composite = pd.to_numeric(
            peer_composite,
            errors="coerce",
        )

        if peer_composite.empty:

            peer_average_values[
                "Composite Score"
            ] = np.nan

        else:

            peer_average_values[
                "Composite Score"
            ] = peer_composite.mean()

        return (
            company_values,
            peer_average_values,
        )

    # -----------------------------------------------------------------
    # Nifty 100 reference for no-peer company
    # -----------------------------------------------------------------

    def build_nifty_average_data(
        self,
        company_id: str,
        peer_percentiles: pd.DataFrame,
        company_scores: pd.DataFrame,
    ):
        """
        Build standalone radar data for a company
        without an assigned peer group.

        Raw financial metrics are converted to a
        common 0-100 scale using the complete
        available financial universe.

        Higher D/E is treated as worse, therefore
        D/E is inversely normalized.
        """

        company_row = company_scores[
            company_scores[
                "company_id"
            ]
            == company_id
        ]

        if company_row.empty:

            return None, None

        company_row = company_row.iloc[0]

        raw_columns = {
            "ROE":
                "return_on_equity_pct",

            "ROCE":
                "return_on_capital_employed_pct",

            "NPM":
                "net_profit_margin_pct",

            "D/E":
                "debt_to_equity",

            "FCF score":
                "free_cash_flow_cr",

            "PAT CAGR 5yr":
                "pat_cagr_5yr",

            "Revenue CAGR 5yr":
                "revenue_cagr_5yr",

            "Composite Score":
                "composite_quality_score",
        }

        company_values = {}
        average_values = {}

        for axis, column in raw_columns.items():

            values = pd.to_numeric(
                company_scores[
                    column
                ],
                errors="coerce",
            )

            valid = values.dropna()

            company_raw = pd.to_numeric(
                company_row[
                    column
                ],
                errors="coerce",
            )

            if pd.isna(company_raw):

                company_score = 50.0

            elif valid.empty:

                company_score = 50.0

            else:

                minimum = valid.min()
                maximum = valid.max()

                if minimum == maximum:

                    company_score = 50.0

                elif axis == "D/E":

                    company_score = (
                        (
                            maximum
                            - company_raw
                        )
                        / (
                            maximum
                            - minimum
                        )
                        * 100
                    )

                else:

                    company_score = (
                        (
                            company_raw
                            - minimum
                        )
                        / (
                            maximum
                            - minimum
                        )
                        * 100
                    )

            # ---------------------------------------------------------
            # Nifty 100 average
            # ---------------------------------------------------------

            if valid.empty:

                average_score = 50.0

            else:

                minimum = valid.min()
                maximum = valid.max()

                if minimum == maximum:

                    average_score = 50.0

                elif axis == "D/E":

                    average_raw = valid.mean()

                    average_score = (
                        (
                            maximum
                            - average_raw
                        )
                        / (
                            maximum
                            - minimum
                        )
                        * 100
                    )

                else:

                    average_raw = valid.mean()

                    average_score = (
                        (
                            average_raw
                            - minimum
                        )
                        / (
                            maximum
                            - minimum
                        )
                        * 100
                    )

            company_values[
                axis
            ] = float(
                np.clip(
                    company_score,
                    0,
                    100,
                )
            )

            average_values[
                axis
            ] = float(
                np.clip(
                    average_score,
                    0,
                    100,
                )
            )

        return (
            company_values,
            average_values,
        )

    # -----------------------------------------------------------------
    # Plot radar
    # -----------------------------------------------------------------

    def plot_radar(
        self,
        company_id: str,
        company_name: str,
        company_values: dict,
        reference_values: dict,
        reference_label: str,
        peer_group: str | None = None,
    ) -> Path:
        """
        Create and save one radar chart.
        """

        labels = RADAR_METRICS

        company_data = [
            float(
                company_values.get(
                    label,
                    50,
                )
            )
            if pd.notna(
                company_values.get(
                    label,
                    np.nan,
                )
            )
            else 50.0
            for label in labels
        ]

        reference_data = [
            float(
                reference_values.get(
                    label,
                    50,
                )
            )
            if pd.notna(
                reference_values.get(
                    label,
                    np.nan,
                )
            )
            else 50.0
            for label in labels
        ]

        number_of_axes = len(labels)

        angles = np.linspace(
            0,
            2 * np.pi,
            number_of_axes,
            endpoint=False,
        ).tolist()

        angles += angles[:1]

        company_data += company_data[:1]
        reference_data += reference_data[:1]

        # -------------------------------------------------------------
        # Figure
        # -------------------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(9, 9),
            subplot_kw={
                "polar": True,
            },
        )

        ax.set_theta_offset(
            np.pi / 2
        )

        ax.set_theta_direction(
            -1
        )

        # -------------------------------------------------------------
        # Company polygon
        # -------------------------------------------------------------

        ax.plot(
            angles,
            company_data,
            linewidth=2.5,
            label=company_name,
        )

        ax.fill(
            angles,
            company_data,
            alpha=0.20,
        )

        # -------------------------------------------------------------
        # Reference polygon
        # -------------------------------------------------------------

        ax.plot(
            angles,
            reference_data,
            linestyle="--",
            linewidth=2.0,
            label=reference_label,
        )

        # -------------------------------------------------------------
        # Axis labels
        # -------------------------------------------------------------

        ax.set_xticks(
            angles[:-1]
        )

        ax.set_xticklabels(
            labels,
            fontsize=11,
        )

        ax.set_ylim(
            0,
            100,
        )

        ax.set_yticks(
            [
                20,
                40,
                60,
                80,
                100,
            ]
        )

        ax.set_yticklabels(
            [
                "20",
                "40",
                "60",
                "80",
                "100",
            ],
            fontsize=9,
        )

        # -------------------------------------------------------------
        # Title
        # -------------------------------------------------------------

        if peer_group:

            title = (
                f"{company_name} ({company_id})\n"
                f"Peer Group: {peer_group}"
            )

        else:

            title = (
                f"{company_name} ({company_id})\n"
                "Nifty 100 Reference"
            )

        ax.set_title(
            title,
            fontsize=15,
            fontweight="bold",
            pad=25,
        )

        ax.legend(
            loc="upper right",
            bbox_to_anchor=(
                1.25,
                1.10,
            ),
            fontsize=10,
        )

        fig.tight_layout()

        # -------------------------------------------------------------
        # Filename
        # -------------------------------------------------------------

        output_file = (
            self.output_dir
            / f"{company_id}_radar.png"
        )

        fig.savefig(
            output_file,
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)

        return output_file

    # -----------------------------------------------------------------
    # Remove stale charts
    # -----------------------------------------------------------------

    def clean_output_directory(
        self,
    ) -> int:
        """
        Remove previously generated radar PNG files.

        This prevents stale files from causing false
        validation results.
        """

        old_files = list(
            self.output_dir.glob(
                "*_radar.png"
            )
        )

        for file in old_files:

            file.unlink()

        return len(old_files)

    # -----------------------------------------------------------------
    # Generate all charts
    # -----------------------------------------------------------------

    def generate_all(
        self,
    ) -> list[Path]:
        """
        Generate radar charts for all companies
        with available financial data.

        Peer companies:
            Company vs peer-group average.

        No-peer companies:
            Company vs Nifty 100 average.

        Companies without financial data:
            Skipped safely.
        """

        peer_percentiles = (
            self.load_peer_percentiles()
        )

        company_scores = (
            self.load_company_scores()
        )

        fcf_history = (
            self.load_fcf_history()
        )

        company_scores = (
            self.calculate_day17_composite_score(
                company_scores,
                fcf_history,
            )
        )

        companies = (
            self.load_companies()
        )

        financial_ids = set(
            company_scores[
                "company_id"
            ]
            .astype(str)
        )

        master_ids = set(
            companies[
                "company_id"
            ]
            .astype(str)
        )

        missing_financial_ids = sorted(
            master_ids
            - financial_ids
        )

        # -------------------------------------------------------------
        # Peer assignments
        # -------------------------------------------------------------

        assignments = (
            peer_percentiles[
                [
                    "company_id",
                    "peer_group_name",
                ]
            ]
            .drop_duplicates()
        )

        assignments[
            "company_id"
        ] = assignments[
            "company_id"
        ].astype(str)

        assignment_map = dict(
            zip(
                assignments[
                    "company_id"
                ],
                assignments[
                    "peer_group_name"
                ],
            )
        )

        financial_peer_ids = (
            set(assignment_map.keys())
            & financial_ids
        )

        financial_no_peer_ids = (
            financial_ids
            - set(assignment_map.keys())
        )

        # -------------------------------------------------------------
        # Clean stale charts
        # -------------------------------------------------------------

        removed_files = (
            self.clean_output_directory()
        )

        # -------------------------------------------------------------
        # Header
        # -------------------------------------------------------------

        print(
            "=" * 70
        )

        print(
            "N100 FINANCIAL INTELLIGENCE PLATFORM"
        )

        print(
            "Sprint 3 - Day 19"
        )

        print(
            "Peer Radar Charts"
        )

        print(
            "=" * 70
        )

        print()

        print(
            "Universe"
        )

        print(
            "-" * 70
        )

        print(
            "Master companies:",
            len(master_ids),
        )

        print(
            "Companies with financial data:",
            len(financial_ids),
        )

        print(
            "Companies with peers:",
            len(financial_peer_ids),
        )

        print(
            "Companies without peers:",
            len(financial_no_peer_ids),
        )

        print(
            "Missing financial data:",
            len(missing_financial_ids),
        )

        if missing_financial_ids:

            print()

            print(
                "Skipped companies:"
            )

            for company_id in (
                missing_financial_ids
            ):

                company_match = companies[
                    companies[
                        "company_id"
                    ]
                    == company_id
                ]

                if company_match.empty:

                    company_name = ""

                else:

                    company_name = str(
                        company_match[
                            "company_name"
                        ].iloc[0]
                    )

                print(
                    f"  - {company_id}"
                    f" ({company_name})"
                )

        print()

        print(
            "Output cleanup"
        )

        print(
            "-" * 70
        )

        print(
            "Removed old radar charts:",
            removed_files,
        )

        generated_files = []

        skipped_count = 0

        peer_chart_count = 0

        nifty_chart_count = 0

        # -------------------------------------------------------------
        # Generate chart for every master company
        # -------------------------------------------------------------

        for _, company in (
            companies.iterrows()
        ):

            company_id = str(
                company[
                    "company_id"
                ]
            )

            company_name = str(
                company[
                    "company_name"
                ]
            )

            # ---------------------------------------------------------
            # Missing financial data
            # ---------------------------------------------------------

            if company_id not in financial_ids:

                skipped_count += 1

                print(
                    f"WARNING: Skipping "
                    f"{company_id} "
                    f"({company_name}) - "
                    f"no financial data."
                )

                continue

            peer_group = (
                assignment_map.get(
                    company_id
                )
            )

            # ---------------------------------------------------------
            # Peer-group chart
            # ---------------------------------------------------------

            if peer_group:

                (
                    company_values,
                    reference_values,
                ) = (
                    self.build_peer_radar_data(
                        company_id,
                        peer_group,
                        peer_percentiles,
                        company_scores,
                    )
                )

                if (
                    company_values is None
                    or reference_values is None
                ):

                    skipped_count += 1

                    print(
                        f"WARNING: Skipping "
                        f"{company_id} - "
                        f"unable to build peer radar."
                    )

                    continue

                reference_label = (
                    f"{peer_group} Average"
                )

                peer_chart_count += 1

            # ---------------------------------------------------------
            # No-peer chart
            # ---------------------------------------------------------

            else:

                (
                    company_values,
                    reference_values,
                ) = (
                    self.build_nifty_average_data(
                        company_id,
                        peer_percentiles,
                        company_scores,
                    )
                )

                if (
                    company_values is None
                    or reference_values is None
                ):

                    skipped_count += 1

                    print(
                        f"WARNING: Skipping "
                        f"{company_id} - "
                        f"unable to build Nifty "
                        f"100 radar."
                    )

                    continue

                reference_label = (
                    "Nifty 100 Average"
                )

                nifty_chart_count += 1

            # ---------------------------------------------------------
            # Plot
            # ---------------------------------------------------------

            output_file = self.plot_radar(
                company_id=company_id,
                company_name=company_name,
                company_values=company_values,
                reference_values=reference_values,
                reference_label=reference_label,
                peer_group=peer_group,
            )

            generated_files.append(
                output_file
            )

        # -------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------

        print()

        print(
            "Radar Charts"
        )

        print(
            "-" * 70
        )

        print(
            "Peer-group charts:",
            peer_chart_count,
        )

        print(
            "Nifty 100 reference charts:",
            nifty_chart_count,
        )

        print(
            "Skipped:",
            skipped_count,
        )

        print(
            "Generated:",
            len(generated_files),
        )

        print(
            "Output directory:",
            self.output_dir,
        )

        return generated_files

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def validate_output(
        self,
        expected_companies: int,
    ) -> None:
        """
        Validate generated PNG files.
        """

        files = sorted(
            self.output_dir.glob(
                "*_radar.png"
            )
        )

        # -------------------------------------------------------------
        # Count validation
        # -------------------------------------------------------------

        if len(files) != expected_companies:

            raise ValueError(
                "Radar chart count validation failed. "
                f"Expected {expected_companies}, "
                f"found {len(files)}."
            )

        # -------------------------------------------------------------
        # Empty-file validation
        # -------------------------------------------------------------

        invalid = [
            file
            for file in files
            if file.stat().st_size == 0
        ]

        if invalid:

            raise ValueError(
                "Empty radar chart files found: "
                f"{invalid}"
            )

        # -------------------------------------------------------------
        # File-size validation
        # -------------------------------------------------------------

        tiny_files = [
            file
            for file in files
            if file.stat().st_size < 1000
        ]

        if tiny_files:

            raise ValueError(
                "Suspiciously small radar chart files "
                f"found: {tiny_files}"
            )

        # -------------------------------------------------------------
        # Filename validation
        # -------------------------------------------------------------

        invalid_names = [
            file
            for file in files
            if not file.name.endswith(
                "_radar.png"
            )
        ]

        if invalid_names:

            raise ValueError(
                "Invalid radar chart filenames: "
                f"{invalid_names}"
            )

        # -------------------------------------------------------------
        # Validation output
        # -------------------------------------------------------------

        print()

        print(
            "Validation"
        )

        print(
            "-" * 70
        )

        print(
            "Expected charts:",
            expected_companies,
        )

        print(
            "Actual charts:",
            len(files),
        )

        print(
            "Empty files:",
            len(invalid),
        )

        print(
            "Suspicious files:",
            len(tiny_files),
        )

        print(
            "Invalid filenames:",
            len(invalid_names),
        )

        print(
            "Status:",
            "PASS",
        )


# =====================================================================
# MAIN
# =====================================================================

def main():

    generator = (
        RadarChartGenerator()
    )

    files = (
        generator.generate_all()
    )

    # -------------------------------------------------------------
    # Expected output
    #
    # Master universe = 92
    # SBIN has no financial data
    # Therefore expected radar charts = 91
    # -------------------------------------------------------------

    expected_charts = 91

    generator.validate_output(
        expected_companies=expected_charts
    )

    print()

    print(
        "=" * 70
    )

    print(
        "DAY 19 RADAR CHARTS "
        "COMPLETED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()