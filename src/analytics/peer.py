"""
N100 Financial Intelligence Platform
Sprint 3 - Day 18

Peer Percentile Rankings

Implements:
- Load peer_groups.xlsx
- Load latest financial metrics
- Compute PERCENT_RANK within each peer group
- 10 peer-ranking metrics
- Inverse percentile for D/E
- Populate peer_percentiles SQLite table
- Graceful handling of companies without peer groups
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


# =====================================================================
# PATHS
# =====================================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = ROOT_DIR / "nifty100.db"

PEER_GROUP_FILE = (
    ROOT_DIR
    / "data"
    / "supporting"
    / "peer_groups.xlsx"
)


# =====================================================================
# METRIC DEFINITIONS
# =====================================================================

METRICS = {
    "ROE": {
        "column": "return_on_equity_pct",
        "higher_is_better": True,
    },

    "ROCE": {
        "column": "return_on_capital_employed_pct",
        "higher_is_better": True,
    },

    "Net Profit Margin": {
        "column": "net_profit_margin_pct",
        "higher_is_better": True,
    },

    "D/E": {
        "column": "debt_to_equity",
        "higher_is_better": False,
    },

    "FCF": {
        "column": "free_cash_flow_cr",
        "higher_is_better": True,
    },

    "PAT CAGR 5yr": {
        "column": "pat_cagr_5yr",
        "higher_is_better": True,
    },

    "Revenue CAGR 5yr": {
        "column": "revenue_cagr_5yr",
        "higher_is_better": True,
    },

    "EPS CAGR 5yr": {
        "column": "eps_cagr_5yr",
        "higher_is_better": True,
    },

    "Interest Coverage": {
        "column": "interest_coverage",
        "higher_is_better": True,
    },

    "Asset Turnover": {
        "column": "asset_turnover",
        "higher_is_better": True,
    },
}


# =====================================================================
# PEER ANALYTICS
# =====================================================================

class PeerPercentileCalculator:
    """
    Calculate percentile rankings for companies within peer groups.
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
        peer_group_file: Path = PEER_GROUP_FILE,
    ):
        self.db_path = Path(db_path)
        self.peer_group_file = Path(
            peer_group_file
        )

    # -----------------------------------------------------------------
    # Load peer groups
    # -----------------------------------------------------------------

    def load_peer_groups(self) -> pd.DataFrame:
        """
        Load peer_groups.xlsx.

        Expected columns:
            company_id
            peer_group_name
        """

        if not self.peer_group_file.exists():
            raise FileNotFoundError(
                "Peer group file not found: "
                f"{self.peer_group_file}"
            )

        df = pd.read_excel(
            self.peer_group_file
        )

        # Normalize column names.
        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            for column in df.columns
        ]

        # -------------------------------------------------------------
        # Detect company ID column
        # -------------------------------------------------------------

        company_candidates = [
            "company_id",
            "companyid",
            "id",
            "ticker",
            "symbol",
        ]

        company_column = next(
            (
                column
                for column in company_candidates
                if column in df.columns
            ),
            None,
        )

        # -------------------------------------------------------------
        # Detect peer-group column
        # -------------------------------------------------------------

        peer_candidates = [
            "peer_group_name",
            "peer_group",
            "peergroup",
            "peer_groupname",
            "group",
        ]

        peer_column = next(
            (
                column
                for column in peer_candidates
                if column in df.columns
            ),
            None,
        )

        if company_column is None:
            raise KeyError(
                "Could not find company ID column in "
                "peer_groups.xlsx. Available columns: "
                f"{df.columns.tolist()}"
            )

        if peer_column is None:
            raise KeyError(
                "Could not find peer group column in "
                "peer_groups.xlsx. Available columns: "
                f"{df.columns.tolist()}"
            )

        result = df[
            [
                company_column,
                peer_column,
            ]
        ].copy()

        result.columns = [
            "company_id",
            "peer_group_name",
        ]

        result["company_id"] = (
            result["company_id"]
            .astype(str)
            .str.strip()
        )

        result["peer_group_name"] = (
            result["peer_group_name"]
            .astype(str)
            .str.strip()
        )

        # Empty / invalid peer assignments become missing.
        result.loc[
            result["peer_group_name"].isin(
                {
                    "",
                    "nan",
                    "none",
                    "null",
                }
            ),
            "peer_group_name",
        ] = pd.NA

        # Remove duplicate company-peer assignments.
        result = (
            result
            .drop_duplicates()
            .reset_index(drop=True)
        )

        return result

    # -----------------------------------------------------------------
    # Load latest financial data
    # -----------------------------------------------------------------

    def load_latest_financial_metrics(
        self,
    ) -> pd.DataFrame:
        """
        Load the latest financial_ratios row for each company.
        """

        with sqlite3.connect(
            self.db_path
        ) as conn:

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
                    company_id,
                    year,
                    return_on_equity_pct,
                    return_on_capital_employed_pct,
                    net_profit_margin_pct,
                    debt_to_equity,
                    free_cash_flow_cr,
                    pat_cagr_5yr,
                    revenue_cagr_5yr,
                    eps_cagr_5yr,
                    interest_coverage,
                    asset_turnover

                FROM ranked

                WHERE rn = 1

                ORDER BY company_id
            """

            df = pd.read_sql_query(
                query,
                conn,
            )

        return df

    # -----------------------------------------------------------------
    # PERCENT_RANK
    # -----------------------------------------------------------------

    @staticmethod
    def calculate_percent_rank(
        series: pd.Series,
        higher_is_better: bool = True,
    ) -> pd.Series:
        """
        Calculate SQL-style PERCENT_RANK.

        Formula:

            (RANK - 1) / (N - 1)

        Result:
            0.00 = lowest
            1.00 = highest

        For D/E:
            lower D/E is better,
            therefore percentile is inverted.
        """

        values = pd.to_numeric(
            series,
            errors="coerce",
        )

        result = pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

        valid = values.notna()

        if not valid.any():
            return result

        valid_values = values.loc[valid]

        # SQL PERCENT_RANK uses competition rank:
        # rank(method="min")
        ranks = valid_values.rank(
            method="min",
            ascending=True,
        )

        count = len(valid_values)

        if count == 1:
            percentile = pd.Series(
                1.0,
                index=valid_values.index,
            )
        else:
            percentile = (
                (ranks - 1)
                / (count - 1)
            )

        # D/E:
        # lower is better.
        if not higher_is_better:
            percentile = 1 - percentile

        result.loc[
            valid_values.index
        ] = percentile

        return result

    # -----------------------------------------------------------------
    # Build percentile dataset
    # -----------------------------------------------------------------

    def calculate_peer_percentiles(
        self,
        peer_groups: pd.DataFrame,
        financial_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate all 10 metric percentiles within each peer group.
        """

        merged = financial_data.merge(
            peer_groups,
            on="company_id",
            how="left",
        )

        # Companies without peer groups are retained,
        # but do not generate peer-ranking rows.
        assigned = merged[
            merged["peer_group_name"].notna()
        ].copy()

        if assigned.empty:
            return pd.DataFrame(
                columns=[
                    "company_id",
                    "peer_group_name",
                    "metric",
                    "value",
                    "percentile_rank",
                    "year",
                ]
            )

        results = []

        # -------------------------------------------------------------
        # Process every peer group
        # -------------------------------------------------------------

        for (
            peer_group_name,
            group,
        ) in assigned.groupby(
            "peer_group_name",
            sort=True,
        ):

            # ---------------------------------------------------------
            # Process all 10 metrics
            # ---------------------------------------------------------

            for metric_name, metric_info in (
                METRICS.items()
            ):

                source_column = metric_info[
                    "column"
                ]

                higher_is_better = (
                    metric_info[
                        "higher_is_better"
                    ]
                )

                if source_column not in group.columns:
                    continue

                values = pd.to_numeric(
                    group[source_column],
                    errors="coerce",
                )

                percentiles = (
                    self.calculate_percent_rank(
                        values,
                        higher_is_better=(
                            higher_is_better
                        ),
                    )
                )

                # -----------------------------------------------------
                # Create long-format rows
                # -----------------------------------------------------

                for index in group.index:

                    value = values.loc[index]
                    percentile = percentiles.loc[
                        index
                    ]

                    if pd.isna(value):
                        continue

                    results.append(
                        {
                            "company_id":
                                group.loc[
                                    index,
                                    "company_id",
                                ],

                            "peer_group_name":
                                peer_group_name,

                            "metric":
                                metric_name,

                            "value":
                                float(value),

                            "percentile_rank":
                                round(
                                    float(
                                        percentile
                                    ),
                                    6,
                                ),

                            "year":
                                group.loc[
                                    index,
                                    "year",
                                ],
                        }
                    )

        return pd.DataFrame(
            results,
            columns=[
                "company_id",
                "peer_group_name",
                "metric",
                "value",
                "percentile_rank",
                "year",
            ],
        )

    # -----------------------------------------------------------------
    # SQLite table
    # -----------------------------------------------------------------

    def create_table(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """
        Create peer_percentiles table.
        """

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS peer_percentiles (
                company_id TEXT NOT NULL,
                peer_group_name TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL,
                percentile_rank REAL,
                year TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_peer_percentiles_company
            ON peer_percentiles(company_id)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_peer_percentiles_group_metric
            ON peer_percentiles(
                peer_group_name,
                metric
            )
            """
        )

        conn.commit()

    # -----------------------------------------------------------------
    # Write to SQLite
    # -----------------------------------------------------------------

    def write_to_database(
        self,
        percentile_data: pd.DataFrame,
    ) -> None:
        """
        Replace existing peer_percentiles data with
        the newly calculated dataset.
        """

        with sqlite3.connect(
            self.db_path
        ) as conn:

            self.create_table(conn)

            # Day 18 is a full rebuild of the ranking table.
            conn.execute(
                "DELETE FROM peer_percentiles"
            )

            if not percentile_data.empty:

                percentile_data.to_sql(
                    "peer_percentiles",
                    conn,
                    if_exists="append",
                    index=False,
                )

            conn.commit()

    # -----------------------------------------------------------------
    # Run complete Day 18 pipeline
    # -----------------------------------------------------------------

    def run(self) -> pd.DataFrame:
        """
        Execute the complete Day 18 pipeline.
        """

        print("=" * 70)
        print(
            "N100 FINANCIAL INTELLIGENCE PLATFORM"
        )
        print("Sprint 3 - Day 18")
        print("Peer Percentile Rankings")
        print("=" * 70)

        # -------------------------------------------------------------
        # Load peer groups
        # -------------------------------------------------------------

        peer_groups = (
            self.load_peer_groups()
        )

        print()
        print("Peer Groups")
        print("-" * 70)

        print(
            "Rows:",
            len(peer_groups),
        )

        print(
            "Companies:",
            peer_groups[
                "company_id"
            ].nunique(),
        )

        print(
            "Peer groups:",
            peer_groups[
                "peer_group_name"
            ].nunique(),
        )

        # -------------------------------------------------------------
        # Financial data
        # -------------------------------------------------------------

        financial_data = (
            self.load_latest_financial_metrics()
        )

        print()
        print("Financial Data")
        print("-" * 70)

        print(
            "Companies:",
            financial_data[
                "company_id"
            ].nunique(),
        )

        # -------------------------------------------------------------
        # Identify companies without peers
        # -------------------------------------------------------------

        assigned_ids = set(
            peer_groups[
                "company_id"
            ]
            .dropna()
            .astype(str)
        )

        universe_ids = set(
            financial_data[
                "company_id"
            ]
            .astype(str)
        )

        no_peer_ids = sorted(
            universe_ids - assigned_ids
        )

        print()
        print("Peer Assignment")
        print("-" * 70)

        print(
            "Assigned:",
            len(
                universe_ids
                & assigned_ids
            ),
        )

        print(
            "No peer group assigned:",
            len(no_peer_ids),
        )

        # -------------------------------------------------------------
        # Calculate rankings
        # -------------------------------------------------------------

        percentile_data = (
            self.calculate_peer_percentiles(
                peer_groups,
                financial_data,
            )
        )

        print()
        print("Percentile Rankings")
        print("-" * 70)

        print(
            "Ranking rows:",
            len(percentile_data),
        )

        print(
            "Companies ranked:",
            percentile_data[
                "company_id"
            ].nunique()
            if not percentile_data.empty
            else 0,
        )

        print(
            "Metrics:",
            percentile_data[
                "metric"
            ].nunique()
            if not percentile_data.empty
            else 0,
        )

        print(
            "Peer groups ranked:",
            percentile_data[
                "peer_group_name"
            ].nunique()
            if not percentile_data.empty
            else 0,
        )

        # -------------------------------------------------------------
        # Write database
        # -------------------------------------------------------------

        self.write_to_database(
            percentile_data
        )

        print()
        print("SQLite")
        print("-" * 70)

        print(
            "Table:",
            "peer_percentiles",
        )

        print(
            "Rows inserted:",
            len(percentile_data),
        )

        # -------------------------------------------------------------
        # Validation
        # -------------------------------------------------------------

        self.validate_database(
            expected_rows=len(
                percentile_data
            )
        )

        print()
        print("=" * 70)
        print(
            "DAY 18 PEER PERCENTILE RANKINGS "
            "COMPLETED SUCCESSFULLY"
        )
        print("=" * 70)

        return percentile_data

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def validate_database(
        self,
        expected_rows: int,
    ) -> None:
        """
        Validate peer_percentiles SQLite output.
        """

        with sqlite3.connect(
            self.db_path
        ) as conn:

            # Row count
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM peer_percentiles
                """
            ).fetchone()[0]

            if count != expected_rows:
                raise ValueError(
                    "peer_percentiles row-count "
                    "validation failed. "
                    f"Expected {expected_rows}, "
                    f"found {count}."
                )

            # Required columns
            columns = pd.read_sql_query(
                """
                PRAGMA table_info(
                    peer_percentiles
                )
                """,
                conn,
            )["name"].tolist()

            required_columns = [
                "company_id",
                "peer_group_name",
                "metric",
                "value",
                "percentile_rank",
                "year",
            ]

            missing = [
                column
                for column in required_columns
                if column not in columns
            ]

            if missing:
                raise ValueError(
                    "Missing peer_percentiles "
                    f"columns: {missing}"
                )

            # Percentile range
            invalid_percentiles = conn.execute(
                """
                SELECT COUNT(*)
                FROM peer_percentiles
                WHERE percentile_rank < 0
                   OR percentile_rank > 1
                """
            ).fetchone()[0]

            if invalid_percentiles != 0:
                raise ValueError(
                    "Found percentile ranks outside "
                    "the 0-1 range."
                )

            # Metric count
            metric_count = conn.execute(
                """
                SELECT COUNT(
                    DISTINCT metric
                )
                FROM peer_percentiles
                """
            ).fetchone()[0]

            if metric_count != 10:
                raise ValueError(
                    "Expected 10 metrics, "
                    f"found {metric_count}."
                )

            # Peer-group count
            peer_count = conn.execute(
                """
                SELECT COUNT(
                    DISTINCT peer_group_name
                )
                FROM peer_percentiles
                """
            ).fetchone()[0]

            if peer_count != 11:
                raise ValueError(
                    "Expected 11 peer groups, "
                    f"found {peer_count}."
                )


# =====================================================================
# MAIN
# =====================================================================

def main():

    calculator = (
        PeerPercentileCalculator()
    )

    calculator.run()


if __name__ == "__main__":
    main()