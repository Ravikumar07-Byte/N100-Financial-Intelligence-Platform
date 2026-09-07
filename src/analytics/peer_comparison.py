"""
N100 Financial Intelligence Platform
Sprint 3 - Day 20

Peer Comparison Excel Report

Implements:
- output/peer_comparison.xlsx
- One worksheet per peer group
- 11 peer-group worksheets
- Company ID and company name
- 20 financial metric columns
- Percentile rank for each metric
- Green / yellow / red percentile formatting
- Gold/amber benchmark company row
- Peer-group median summary row
- Workbook validation
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# =====================================================================
# PATHS
# =====================================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = ROOT_DIR / "nifty100.db"

OUTPUT_DIR = ROOT_DIR / "output"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "peer_comparison.xlsx"
)


# =====================================================================
# EXPECTED PEER GROUPS
# =====================================================================

EXPECTED_PEER_GROUPS = [
    "Automobiles",
    "Consumer Finance",
    "FMCG",
    "IT Services",
    "Life Insurance",
    "Oil & Gas",
    "Pharmaceuticals",
    "Power & Utilities",
    "Private Banks",
    "Public Sector Banks",
    "Steel",
]


# =====================================================================
# 20 DAY-20 METRICS
# =====================================================================

METRICS = [
    "ROE",
    "ROCE",
    "Net Profit Margin",
    "Operating Profit Margin",
    "D/E",
    "Interest Coverage",
    "Asset Turnover",
    "Free Cash Flow",
    "Cash From Operations",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "EPS CAGR 5yr",
    "Net Profit",
    "Sales",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "Dividend Yield",
    "Dividend Payout",
    "Composite Score",
]


# =====================================================================
# PERCENTILE COLUMN NAMES
# =====================================================================

PERCENTILE_COLUMNS = [
    f"{metric} Percentile"
    for metric in METRICS
]


# =====================================================================
# DATABASE METRIC MAPPING
# =====================================================================

FINANCIAL_METRIC_MAP = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "Operating Profit Margin": "operating_profit_margin_pct",
    "D/E": "debt_to_equity",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
    "Free Cash Flow": "free_cash_flow_cr",
    "Cash From Operations": "cash_from_operations_cr",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Net Profit": "net_profit",
    "Sales": "sales",
    "P/E": "pe_ratio",
    "P/B": "pb_ratio",
    "EV/EBITDA": "ev_ebitda",
    "Dividend Yield": "dividend_yield_pct",
    "Dividend Payout": "dividend_payout_ratio_pct",
    "Composite Score": "composite_quality_score",
}


# =====================================================================
# EXCEL STYLING
# =====================================================================

GREEN_FILL = PatternFill(
    fill_type="solid",
    fgColor="C6EFCE",
)

YELLOW_FILL = PatternFill(
    fill_type="solid",
    fgColor="FFEB9C",
)

RED_FILL = PatternFill(
    fill_type="solid",
    fgColor="FFC7CE",
)

BENCHMARK_FILL = PatternFill(
    fill_type="solid",
    fgColor="FFD966",
)

HEADER_FILL = PatternFill(
    fill_type="solid",
    fgColor="1F4E78",
)

SUMMARY_FILL = PatternFill(
    fill_type="solid",
    fgColor="D9EAF7",
)

WHITE_FONT = Font(
    color="FFFFFF",
    bold=True,
)

BOLD_FONT = Font(
    bold=True,
)

THIN_BORDER = Border(
    bottom=Side(
        style="thin",
        color="D9E1F2",
    )
)


# =====================================================================
# REPORT GENERATOR
# =====================================================================

class PeerComparisonReport:
    """
    Generate Sprint 3 Day 20 peer comparison workbook.
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
        output_file: Path = OUTPUT_FILE,
    ):
        self.db_path = Path(db_path)
        self.output_file = Path(output_file)

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    # -----------------------------------------------------------------
    # Database connection
    # -----------------------------------------------------------------

    def connection(self):
        return sqlite3.connect(
            self.db_path
        )

    # -----------------------------------------------------------------
    # Load peer groups
    # -----------------------------------------------------------------

    def load_peer_groups(self):
        """
        Load peer-group assignments and benchmark flags.
        """

        with self.connection() as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    peer_group_name,
                    company_id,
                    is_benchmark
                FROM peer_groups
                ORDER BY
                    peer_group_name,
                    company_id
                """,
                conn,
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        df["is_benchmark"] = (
            pd.to_numeric(
                df["is_benchmark"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

        return df

    # -----------------------------------------------------------------
    # Load companies
    # -----------------------------------------------------------------

    def load_companies(self):
        """
        Load company names.
        """

        with self.connection() as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    id AS company_id,
                    company_name
                FROM companies
                """,
                conn,
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        return df

    # -----------------------------------------------------------------
    # Load latest financial data
    # -----------------------------------------------------------------

    def load_financial_data(self):
        """
        Load latest financial-ratio and market data
        for each company.
        """

        with self.connection() as conn:

            query = """
                WITH financial_ranked AS (
                    SELECT
                        fr.*,

                        ROW_NUMBER() OVER (
                            PARTITION BY fr.company_id
                            ORDER BY fr.year DESC
                        ) AS rn

                    FROM financial_ratios fr
                ),

                market_ranked AS (
                    SELECT
                        mc.*,

                        ROW_NUMBER() OVER (
                            PARTITION BY mc.company_id
                            ORDER BY mc.year DESC
                        ) AS rn

                    FROM market_cap mc
                ),

                pnl_ranked AS (
                    SELECT
                        pl.*,

                        ROW_NUMBER() OVER (
                            PARTITION BY pl.company_id
                            ORDER BY pl.year DESC
                        ) AS rn

                    FROM profitandloss pl
                )

                SELECT

                    f.company_id,

                    f.return_on_equity_pct,

                    f.return_on_capital_employed_pct,

                    f.net_profit_margin_pct,

                    f.operating_profit_margin_pct,

                    f.debt_to_equity,

                    f.interest_coverage,

                    f.asset_turnover,

                    f.free_cash_flow_cr,

                    f.cash_from_operations_cr,

                    f.pat_cagr_5yr,

                    f.revenue_cagr_5yr,

                    f.eps_cagr_5yr,

                    f.composite_quality_score,

                    m.pe_ratio,

                    m.pb_ratio,

                    m.ev_ebitda,

                    m.dividend_yield_pct,

                    m.market_cap_crore,

                    p.net_profit,

                    p.sales,

                    p.dividend_payout

                FROM financial_ranked f

                LEFT JOIN market_ranked m
                    ON f.company_id = m.company_id
                    AND m.rn = 1

                LEFT JOIN pnl_ranked p
                    ON f.company_id = p.company_id
                    AND p.rn = 1

                WHERE f.rn = 1

                ORDER BY f.company_id
            """

            df = pd.read_sql_query(
                query,
                conn,
            )

        df["company_id"] = (
            df["company_id"]
            .astype(str)
        )

        # Rename source columns to report columns.
        df = df.rename(
            columns={
                "return_on_equity_pct":
                    "ROE",

                "return_on_capital_employed_pct":
                    "ROCE",

                "net_profit_margin_pct":
                    "Net Profit Margin",

                "operating_profit_margin_pct":
                    "Operating Profit Margin",

                "debt_to_equity":
                    "D/E",

                "interest_coverage":
                    "Interest Coverage",

                "asset_turnover":
                    "Asset Turnover",

                "free_cash_flow_cr":
                    "Free Cash Flow",

                "cash_from_operations_cr":
                    "Cash From Operations",

                "pat_cagr_5yr":
                    "PAT CAGR 5yr",

                "revenue_cagr_5yr":
                    "Revenue CAGR 5yr",

                "eps_cagr_5yr":
                    "EPS CAGR 5yr",

                "net_profit":
                    "Net Profit",

                "sales":
                    "Sales",

                "pe_ratio":
                    "P/E",

                "pb_ratio":
                    "P/B",

                "ev_ebitda":
                    "EV/EBITDA",

                "dividend_yield_pct":
                    "Dividend Yield",

                "dividend_payout":
                    "Dividend Payout",

                "composite_quality_score":
                    "Composite Score",
            }
        )

        # Ensure every expected metric exists.
        for metric in METRICS:

            if metric not in df.columns:

                df[metric] = np.nan

            df[metric] = pd.to_numeric(
                df[metric],
                errors="coerce",
            )

        return df[
            [
                "company_id",
                *METRICS,
            ]
        ]

    # -----------------------------------------------------------------
    # Calculate peer percentiles
    # -----------------------------------------------------------------

    def calculate_percentiles(
        self,
        group_df: pd.DataFrame,
    ):
        """
        Calculate percentile rank for every metric
        inside a peer group.

        Uses the same 0-1 percentile concept as
        Day 18.

        D/E is inverted because lower debt-to-equity
        is better.
        """

        result = group_df.copy()

        for metric in METRICS:

            values = pd.to_numeric(
                result[metric],
                errors="coerce",
            )

            valid = values.notna()

            result[
                f"{metric} Percentile"
            ] = np.nan

            if valid.sum() == 0:
                continue

            valid_values = (
                values[valid]
            )

            if valid_values.nunique() == 1:

                ranks = pd.Series(
                    1.0,
                    index=valid_values.index,
                )

            else:

                ranks = (
                    valid_values
                    .rank(
                        method="min",
                        ascending=True,
                    )
                    - 1
                ) / (
                    len(valid_values) - 1
                )

            if metric == "D/E":

                ranks = 1 - ranks

            result.loc[
                valid,
                f"{metric} Percentile"
            ] = ranks

        return result

    # -----------------------------------------------------------------
    # Build peer-group dataframe
    # -----------------------------------------------------------------

    def build_group_dataframe(
        self,
        peer_group,
        assignments,
        financial_data,
        companies,
    ):
        """
        Build one peer-group worksheet dataframe.
        """

        group_assignments = assignments[
            assignments[
                "peer_group_name"
            ]
            == peer_group
        ].copy()

        df = group_assignments.merge(
            companies,
            on="company_id",
            how="left",
        )

        df = df.merge(
            financial_data,
            on="company_id",
            how="left",
        )

        # Preserve benchmark information separately.
        benchmark_map = dict(
            zip(
                df["company_id"],
                df["is_benchmark"],
            )
        )

        # Calculate percentile ranks.
        df = self.calculate_percentiles(
            df
        )

        # Required output ordering.
        output_columns = [
            "company_id",
            "company_name",
            *METRICS,
            *PERCENTILE_COLUMNS,
        ]

        df = df[
            output_columns
        ]

        return (
            df,
            benchmark_map,
        )

    # -----------------------------------------------------------------
    # Add summary row
    # -----------------------------------------------------------------

    def add_median_row(
        self,
        worksheet,
        data_start_row,
        data_end_row,
    ):
        """
        Add peer-group median summary row.
        """

        summary_row = (
            data_end_row + 1
        )

        worksheet.cell(
            row=summary_row,
            column=1,
            value="Peer Median",
        )

        worksheet.cell(
            row=summary_row,
            column=1,
        ).font = BOLD_FONT

        worksheet.cell(
            row=summary_row,
            column=1,
        ).fill = SUMMARY_FILL

        worksheet.cell(
            row=summary_row,
            column=2,
            value="Peer Group Median",
        )

        worksheet.cell(
            row=summary_row,
            column=2,
        ).font = BOLD_FONT

        worksheet.cell(
            row=summary_row,
            column=2,
        ).fill = SUMMARY_FILL

        # -------------------------------------------------------------
        # Median for 20 financial metrics.
        # -------------------------------------------------------------

        for metric_index, metric in enumerate(
            METRICS,
            start=3,
        ):

            column_letter = (
                get_column_letter(
                    metric_index
                )
            )

            cell = worksheet.cell(
                row=summary_row,
                column=metric_index,
            )

            cell.value = (
                f"=MEDIAN("
                f"{column_letter}"
                f"{data_start_row}:"
                f"{column_letter}"
                f"{data_end_row})"
            )

            cell.font = BOLD_FONT
            cell.fill = SUMMARY_FILL

        # -------------------------------------------------------------
        # Percentile median.
        # -------------------------------------------------------------

        percentile_start = (
            3 + len(METRICS)
        )

        for offset in range(
            len(PERCENTILE_COLUMNS)
        ):

            column_index = (
                percentile_start
                + offset
            )

            column_letter = (
                get_column_letter(
                    column_index
                )
            )

            cell = worksheet.cell(
                row=summary_row,
                column=column_index,
            )

            cell.value = (
                f"=MEDIAN("
                f"{column_letter}"
                f"{data_start_row}:"
                f"{column_letter}"
                f"{data_end_row})"
            )

            cell.font = BOLD_FONT
            cell.fill = SUMMARY_FILL

        return summary_row

    # -----------------------------------------------------------------
    # Format worksheet
    # -----------------------------------------------------------------

    def format_worksheet(
        self,
        worksheet,
        dataframe,
        benchmark_map,
        data_start_row,
        data_end_row,
    ):
        """
        Apply all Day 20 Excel formatting.
        """

        # -------------------------------------------------------------
        # Header formatting
        # -------------------------------------------------------------

        for cell in worksheet[1]:

            cell.fill = HEADER_FILL
            cell.font = WHITE_FONT
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        worksheet.freeze_panes = "C2"

        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

        # -------------------------------------------------------------
        # Percentile columns
        # -------------------------------------------------------------

        percentile_start = (
            3 + len(METRICS)
        )

        for row in range(
            data_start_row,
            data_end_row + 1,
        ):

            # ---------------------------------------------------------
            # Benchmark row
            # ---------------------------------------------------------

            company_id = str(
                worksheet.cell(
                    row=row,
                    column=1,
                ).value
            )

            is_benchmark = (
                benchmark_map.get(
                    company_id,
                    0,
                )
                == 1
            )

            # ---------------------------------------------------------
            # Percentile colors
            #
            # Benchmark highlighting is applied to
            # the company row first, but percentile
            # cells retain their percentile color so
            # the rank information remains visible.
            # ---------------------------------------------------------

            for offset in range(
                len(PERCENTILE_COLUMNS)
            ):

                column_index = (
                    percentile_start
                    + offset
                )

                cell = worksheet.cell(
                    row=row,
                    column=column_index,
                )

                value = cell.value

                if value is None:
                    continue

                try:

                    percentile = float(
                        value
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

                # Day 18 percentile_rank is 0-1.
                # Convert to percentage for
                # display and formatting.

                percentage = (
                    percentile * 100
                )

                if percentage >= 75:

                    cell.fill = (
                        GREEN_FILL
                    )

                elif percentage <= 25:

                    cell.fill = (
                        RED_FILL
                    )

                else:

                    cell.fill = (
                        YELLOW_FILL
                    )

                cell.number_format = (
                    "0.0"
                )

            # ---------------------------------------------------------
            # Benchmark row background.
            #
            # Apply amber to identity and metric
            # cells. Percentile cells retain rank
            # colors to satisfy percentile formatting.
            # ---------------------------------------------------------

            if is_benchmark:

                for column in range(
                    1,
                    percentile_start,
                ):

                    cell = worksheet.cell(
                        row=row,
                        column=column,
                    )

                    cell.fill = (
                        BENCHMARK_FILL
                    )

                    cell.font = BOLD_FONT

        # -------------------------------------------------------------
        # Number formatting
        # -------------------------------------------------------------

        for row in range(
            data_start_row,
            data_end_row + 1,
        ):

            for column in range(
                3,
                percentile_start,
            ):

                cell = worksheet.cell(
                    row=row,
                    column=column,
                )

                if isinstance(
                    cell.value,
                    (int, float),
                ):

                    cell.number_format = (
                        "0.00"
                    )

        # -------------------------------------------------------------
        # Borders
        # -------------------------------------------------------------

        for row in worksheet.iter_rows():

            for cell in row:

                cell.border = THIN_BORDER

        # -------------------------------------------------------------
        # Column widths
        # -------------------------------------------------------------

        worksheet.column_dimensions[
            "A"
        ].width = 18

        worksheet.column_dimensions[
            "B"
        ].width = 28

        for column in range(
            3,
            3 + len(METRICS),
        ):

            worksheet.column_dimensions[
                get_column_letter(
                    column
                )
            ].width = 18

        for column in range(
            percentile_start,
            percentile_start
            + len(PERCENTILE_COLUMNS),
        ):

            worksheet.column_dimensions[
                get_column_letter(
                    column
                )
            ].width = 19

        worksheet.row_dimensions[
            1
        ].height = 42

    # -----------------------------------------------------------------
    # Generate workbook
    # -----------------------------------------------------------------

    def generate(
        self,
    ):
        """
        Generate complete peer comparison workbook.
        """

        assignments = (
            self.load_peer_groups()
        )

        companies = (
            self.load_companies()
        )

        financial_data = (
            self.load_financial_data()
        )

        print(
            "=" * 70
        )

        print(
            "N100 FINANCIAL INTELLIGENCE PLATFORM"
        )

        print(
            "Sprint 3 - Day 20"
        )

        print(
            "Peer Comparison Excel Report"
        )

        print(
            "=" * 70
        )

        print()

        print(
            "Peer Groups"
        )

        print(
            "-" * 70
        )

        print(
            "Total peer groups:",
            assignments[
                "peer_group_name"
            ].nunique(),
        )

        print(
            "Total assignments:",
            len(assignments),
        )

        print()

        # -------------------------------------------------------------
        # Validate peer groups
        # -------------------------------------------------------------

        actual_groups = sorted(
            assignments[
                "peer_group_name"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        expected_groups = sorted(
            EXPECTED_PEER_GROUPS
        )

        if actual_groups != expected_groups:

            raise ValueError(
                "Peer-group mismatch.\n"
                f"Expected: {expected_groups}\n"
                f"Found: {actual_groups}"
            )

        # -------------------------------------------------------------
        # Remove existing workbook
        # -------------------------------------------------------------

        if self.output_file.exists():

            self.output_file.unlink()

        # -------------------------------------------------------------
        # Create workbook
        # -------------------------------------------------------------

        with pd.ExcelWriter(
            self.output_file,
            engine="openpyxl",
        ) as writer:

            for peer_group in (
                EXPECTED_PEER_GROUPS
            ):

                print(
                    f"Generating: {peer_group}"
                )

                (
                    group_df,
                    benchmark_map,
                ) = (
                    self.build_group_dataframe(
                        peer_group,
                        assignments,
                        financial_data,
                        companies,
                    )
                )

                # -----------------------------------------------------
                # Write dataframe
                # -----------------------------------------------------

                group_df.to_excel(
                    writer,
                    sheet_name=peer_group[
                        :31
                    ],
                    index=False,
                )

                worksheet = (
                    writer.book[
                        peer_group[:31]
                    ]
                )

                data_start_row = 2

                data_end_row = (
                    1 + len(group_df)
                )

                # -----------------------------------------------------
                # Add median row
                # -----------------------------------------------------

                summary_row = (
                    self.add_median_row(
                        worksheet,
                        data_start_row,
                        data_end_row,
                    )
                )

                # -----------------------------------------------------
                # Format
                # -----------------------------------------------------

                self.format_worksheet(
                    worksheet,
                    group_df,
                    benchmark_map,
                    data_start_row,
                    data_end_row,
                )

                # -----------------------------------------------------
                # Summary row formatting
                # -----------------------------------------------------

                for cell in worksheet[
                    summary_row
                ]:

                    cell.fill = (
                        SUMMARY_FILL
                    )

                    cell.font = BOLD_FONT

        print()

        print(
            "Workbook created:"
        )

        print(
            self.output_file
        )

        return self.output_file

    # -----------------------------------------------------------------
    # Validate workbook
    # -----------------------------------------------------------------

    def validate(
        self,
    ):
        """
        Validate Day 20 workbook.
        """

        if not self.output_file.exists():

            raise ValueError(
                "peer_comparison.xlsx was not created."
            )

        workbook = load_workbook(
            self.output_file,
            data_only=False,
        )

        sheets = workbook.sheetnames

        expected_sheets = [
            group[:31]
            for group in EXPECTED_PEER_GROUPS
        ]

        # -------------------------------------------------------------
        # Sheet count
        # -------------------------------------------------------------

        if len(sheets) != 11:

            raise ValueError(
                "Expected 11 sheets, "
                f"found {len(sheets)}."
            )

        if sheets != expected_sheets:

            raise ValueError(
                "Unexpected sheet names.\n"
                f"Expected: {expected_sheets}\n"
                f"Found: {sheets}"
            )

        # -------------------------------------------------------------
        # Column validation
        # -------------------------------------------------------------

        expected_columns = [
            "company_id",
            "company_name",
            *METRICS,
            *PERCENTILE_COLUMNS,
        ]

        for sheet_name in sheets:

            worksheet = workbook[
                sheet_name
            ]

            headers = [
                cell.value
                for cell in worksheet[1]
            ]

            if headers != expected_columns:

                raise ValueError(
                    f"Column mismatch in "
                    f"{sheet_name}.\n"
                    f"Expected {len(expected_columns)} "
                    f"columns, found {len(headers)}."
                )

            if len(headers) != 42:

                raise ValueError(
                    f"{sheet_name}: expected 42 "
                    f"columns, found {len(headers)}."
                )

        # -------------------------------------------------------------
        # Benchmark validation
        # -------------------------------------------------------------

        benchmark_count = 0

        for sheet_name in sheets:

            worksheet = workbook[
                sheet_name
            ]

            # Summary row is last row.
            summary_row = (
                worksheet.max_row
            )

            # Data rows start at 2.
            for row in range(
                2,
                summary_row,
            ):

                company_id = (
                    worksheet.cell(
                        row=row,
                        column=1,
                    ).value
                )

                # Gold benchmark fill on metric/identity area.
                fill_color = (
                    worksheet.cell(
                        row=row,
                        column=1,
                    ).fill.fgColor.rgb
                )

                if fill_color in {
                    "00FFD966",
                    "FFD966",
                }:

                    benchmark_count += 1

            # Summary row check.
            summary_value = (
                worksheet.cell(
                    row=summary_row,
                    column=1,
                ).value
            )

            if summary_value != "Peer Median":

                raise ValueError(
                    f"{sheet_name}: missing "
                    "Peer Median summary row."
                )

        if benchmark_count != 11:

            raise ValueError(
                "Expected exactly one benchmark "
                f"per sheet. Found {benchmark_count}."
            )

        # -------------------------------------------------------------
        # Percentile validation
        # -------------------------------------------------------------

        invalid_percentiles = 0

        percentile_start = (
            3 + len(METRICS)
        )

        for sheet_name in sheets:

            worksheet = workbook[
                sheet_name
            ]

            # Exclude header and summary row.
            for row in range(
                2,
                worksheet.max_row,
            ):

                for column in range(
                    percentile_start,
                    percentile_start
                    + len(PERCENTILE_COLUMNS),
                ):

                    value = worksheet.cell(
                        row=row,
                        column=column,
                    ).value

                    if value is None:

                        continue

                    try:

                        value = float(
                            value
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        invalid_percentiles += 1
                        continue

                    if not (
                        0 <= value <= 1
                    ):

                        invalid_percentiles += 1

        if invalid_percentiles:

            raise ValueError(
                "Invalid percentile values found: "
                f"{invalid_percentiles}"
            )

        # -------------------------------------------------------------
        # Final validation
        # -------------------------------------------------------------

        workbook.close()

        print()

        print(
            "Validation"
        )

        print(
            "-" * 70
        )

        print(
            "Workbook exists:",
            "PASS",
        )

        print(
            "Sheets:",
            len(sheets),
        )

        print(
            "Expected sheets:",
            11,
        )

        print(
            "Columns per sheet:",
            42,
        )

        print(
            "Benchmark rows:",
            benchmark_count,
        )

        print(
            "Invalid percentile values:",
            invalid_percentiles,
        )

        print(
            "Peer Median rows:",
            11,
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
        PeerComparisonReport()
    )

    generator.generate()

    generator.validate()

    print()

    print(
        "=" * 70
    )

    print(
        "DAY 20 PEER COMPARISON "
        "REPORT COMPLETED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()