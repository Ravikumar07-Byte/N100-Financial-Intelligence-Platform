"""
N100 Financial Intelligence Platform
Sprint 3 - Day 15
Screener Engine Core

Loads screener configuration from YAML, combines the required
financial tables, applies screener filters, and returns a
company-level screened DataFrame.
"""

from pathlib import Path
import sqlite3

import pandas as pd
import yaml


# -------------------------------------------------------------------
# Project paths
# -------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = ROOT_DIR / "nifty100.db"
CONFIG_PATH = ROOT_DIR / "config" / "screener_config.yaml"


class ScreenerEngine:
    """Core financial screener engine."""

    # ----------------------------------------------------------------
    # Initialization
    # ----------------------------------------------------------------

    def __init__(
        self,
        db_path: str | Path = DB_PATH,
        config_path: str | Path = CONFIG_PATH,
    ):
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)

        self.config = self._load_config()

    # ----------------------------------------------------------------
    # Configuration
    # ----------------------------------------------------------------

    def _load_config(self) -> dict:
        """Load screener configuration from YAML."""

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Screener configuration not found: "
                f"{self.config_path}"
            )

        with open(
            self.config_path,
            "r",
            encoding="utf-8",
        ) as file:
            config = yaml.safe_load(file)

        if not config or "screeners" not in config:
            raise ValueError(
                "Invalid screener configuration: "
                "'screeners' section missing."
            )

        return config

    def get_screener_names(self) -> list[str]:
        """Return configured screener keys."""

        return list(
            self.config["screeners"].keys()
        )

    def get_screener_config(
        self,
        screener_name: str,
    ) -> dict:
        """Return configuration for one screener."""

        screeners = self.config["screeners"]

        if screener_name not in screeners:
            raise ValueError(
                f"Unknown screener '{screener_name}'. "
                f"Available: {list(screeners.keys())}"
            )

        return screeners[screener_name]

    # ----------------------------------------------------------------
    # Database
    # ----------------------------------------------------------------

    def _connect(self):
        """Create SQLite connection."""

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}"
            )

        return sqlite3.connect(self.db_path)

    # ----------------------------------------------------------------
    # Latest-year universe
    # ----------------------------------------------------------------

    def load_universe(self) -> pd.DataFrame:
        """
        Load the latest available financial record for each company.

        Combines:
        - companies
        - sectors
        - financial_ratios
        - market_cap
        - profitandloss

        Returns:
            DataFrame containing one latest-year row per company.
        """

        query = """
        WITH latest_ratios AS (
            SELECT *
            FROM (
                SELECT
                    fr.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY fr.company_id
                        ORDER BY fr.year DESC
                    ) AS rn
                FROM financial_ratios fr
            )
            WHERE rn = 1
        ),

        latest_market AS (
            SELECT *
            FROM (
                SELECT
                    mc.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY mc.company_id
                        ORDER BY mc.year DESC
                    ) AS rn
                FROM market_cap mc
            )
            WHERE rn = 1
        ),

        latest_pnl AS (
            SELECT *
            FROM (
                SELECT
                    pl.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY pl.company_id
                        ORDER BY pl.year DESC
                    ) AS rn
                FROM profitandloss pl
            )
            WHERE rn = 1
        )

        SELECT
            c.id AS company_id,
            c.company_name,

            s.broad_sector,
            s.sub_sector,

            fr.year AS ratio_year,

            fr.net_profit_margin_pct,
            fr.operating_profit_margin_pct,

            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,
            fr.return_on_assets_pct,

            fr.debt_to_equity,
            fr.interest_coverage,

            fr.free_cash_flow_cr,
            fr.capex_cr,
            fr.cash_from_operations_cr,

            fr.total_debt_cr,
            fr.net_debt,

            fr.earnings_per_share,
            fr.book_value_per_share,

            fr.dividend_payout_ratio_pct,

            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.eps_cagr_5yr,

            mc.market_cap_crore,
            mc.enterprise_value_crore,

            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct,

            pl.sales,
            pl.net_profit,
            pl.operating_profit,
            pl.eps AS pnl_eps,

            CASE
                WHEN s.broad_sector = 'Financials'
                    THEN 0
                ELSE 1
            END AS debt_filter_allowed

        FROM companies c

        LEFT JOIN sectors s
            ON s.company_id = c.id

        LEFT JOIN latest_ratios fr
            ON fr.company_id = c.id

        LEFT JOIN latest_market mc
            ON mc.company_id = c.id

        LEFT JOIN latest_pnl pl
            ON pl.company_id = c.id
        """

        with self._connect() as conn:
            df = pd.read_sql_query(
                query,
                conn,
            )

        return df

    # ----------------------------------------------------------------
    # Historical data
    # ----------------------------------------------------------------

    def load_historical_metrics(self) -> pd.DataFrame:
        """
        Load historical sales and debt-to-equity data.

        Used by Turnaround Watch.
        """

        query = """
        SELECT
            fr.company_id,
            fr.year,
            fr.debt_to_equity,
            pl.sales

        FROM financial_ratios fr

        LEFT JOIN profitandloss pl
            ON pl.company_id = fr.company_id
            AND pl.year = fr.year

        ORDER BY
            fr.company_id,
            fr.year
        """

        with self._connect() as conn:
            df = pd.read_sql_query(
                query,
                conn,
            )

        return df

    def calculate_turnaround_metrics(
        self,
        historical_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate Turnaround Watch metrics.

        Metrics:
        - Revenue CAGR over latest 3-year period
        - YoY D/E declining flag
        """

        results = []

        for company_id, group in historical_df.groupby(
            "company_id"
        ):

            group = group.copy()

            # --------------------------------------------------------
            # Convert year into sortable date
            # --------------------------------------------------------

            group["year_date"] = pd.to_datetime(
                group["year"],
                format="%Y-%m",
                errors="coerce",
            )

            group = group.sort_values(
                "year_date"
            )

            # --------------------------------------------------------
            # 3-year Revenue CAGR
            # --------------------------------------------------------

            sales_data = group[
                group["sales"].notna()
                & (group["sales"] > 0)
            ].copy()

            revenue_cagr_3yr = None

            if len(sales_data) >= 4:

                first_sales = sales_data.iloc[-4]["sales"]
                latest_sales = sales_data.iloc[-1]["sales"]

                if (
                    pd.notna(first_sales)
                    and pd.notna(latest_sales)
                    and first_sales > 0
                    and latest_sales > 0
                ):
                    revenue_cagr_3yr = (
                        (
                            latest_sales
                            / first_sales
                        )
                        ** (1 / 3)
                        - 1
                    ) * 100

            # --------------------------------------------------------
            # YoY D/E declining
            # --------------------------------------------------------

            debt_data = group[
                group["debt_to_equity"].notna()
            ].copy()

            debt_to_equity_declining = False

            if len(debt_data) >= 2:

                previous_de = debt_data.iloc[-2][
                    "debt_to_equity"
                ]

                latest_de = debt_data.iloc[-1][
                    "debt_to_equity"
                ]

                if (
                    pd.notna(previous_de)
                    and pd.notna(latest_de)
                ):
                    debt_to_equity_declining = (
                        latest_de < previous_de
                    )

            results.append(
                {
                    "company_id": company_id,
                    "revenue_cagr_3yr": revenue_cagr_3yr,
                    "debt_to_equity_declining":
                        debt_to_equity_declining,
                }
            )

        return pd.DataFrame(results)

    # ----------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------

    @staticmethod
    def _positive(value) -> bool:
        """Return True when value is positive."""

        return (
            pd.notna(value)
            and value > 0
        )

    @staticmethod
    def _debt_free(value) -> bool:
        """Return True when D/E is zero or below."""

        if pd.isna(value):
            return False

        return value <= 0

    # ----------------------------------------------------------------
    # D/E filter
    # ----------------------------------------------------------------

    def _apply_debt_to_equity_filter(
        self,
        df: pd.DataFrame,
        maximum: float,
    ) -> pd.DataFrame:
        """
        Apply D/E filter.

        Financial companies are excluded from the D/E test
        because D/E is not directly comparable for financial
        institutions.

        For maximum = 0, debt-free logic is used.
        """

        result = df.copy()

        financial_mask = (
            result["broad_sector"]
            .fillna("")
            .eq("Financials")
        )

        non_financial_mask = ~financial_mask

        if maximum == 0:

            debt_mask = (
                result["debt_to_equity"]
                .apply(self._debt_free)
            )

        else:

            debt_mask = (
                result["debt_to_equity"]
                < maximum
            )

        final_mask = (
            financial_mask
            | (
                non_financial_mask
                & debt_mask
            )
        )

        return result[final_mask]

    # ----------------------------------------------------------------
    # Screener filters
    # ----------------------------------------------------------------

    def apply_filters(
        self,
        df: pd.DataFrame,
        screener_name: str,
    ) -> pd.DataFrame:
        """
        Apply configured screener filters.
        """

        config = self.get_screener_config(
            screener_name
        )

        filters = config.get(
            "filters",
            {},
        )

        result = df.copy()

        # ============================================================
        # QUALITY COMPOUNDER
        # ============================================================

        if "roe_min" in filters:

            result = result[
                result["return_on_equity_pct"]
                > filters["roe_min"]
            ]

        if "debt_to_equity_max" in filters:

            result = self._apply_debt_to_equity_filter(
                result,
                filters["debt_to_equity_max"],
            )

        if "free_cash_flow_min" in filters:

            result = result[
                result["free_cash_flow_cr"]
                > filters["free_cash_flow_min"]
            ]

        if "revenue_cagr_5yr_min" in filters:

            result = result[
                result["revenue_cagr_5yr"]
                > filters["revenue_cagr_5yr_min"]
            ]

        # ============================================================
        # VALUE PICK
        # ============================================================

        if "pe_max" in filters:

            result = result[
                result["pe_ratio"]
                < filters["pe_max"]
            ]

        if "pb_max" in filters:

            result = result[
                result["pb_ratio"]
                < filters["pb_max"]
            ]

        if "dividend_yield_min" in filters:

            result = result[
                result["dividend_yield_pct"]
                > filters["dividend_yield_min"]
            ]

        if "debt_to_equity_max" in filters:

            # Value Pick has D/E < 2.
            result = self._apply_debt_to_equity_filter(
                result,
                filters["debt_to_equity_max"],
            )

        # ============================================================
        # GROWTH ACCELERATOR
        # ============================================================

        if "pat_cagr_5yr_min" in filters:

            result = result[
                result["pat_cagr_5yr"]
                > filters["pat_cagr_5yr_min"]
            ]

        if "revenue_cagr_5yr_min" in filters:

            result = result[
                result["revenue_cagr_5yr"]
                > filters["revenue_cagr_5yr_min"]
            ]

        if "debt_to_equity_max" in filters:

            result = self._apply_debt_to_equity_filter(
                result,
                filters["debt_to_equity_max"],
            )

        # ============================================================
        # DIVIDEND CHAMPION
        # ============================================================

        if "dividend_yield_min" in filters:

            result = result[
                result["dividend_yield_pct"]
                > filters["dividend_yield_min"]
            ]

        if "dividend_payout_ratio_max" in filters:

            result = result[
                result["dividend_payout_ratio_pct"]
                < filters[
                    "dividend_payout_ratio_max"
                ]
            ]

        if "free_cash_flow_min" in filters:

            result = result[
                result["free_cash_flow_cr"]
                > filters["free_cash_flow_min"]
            ]

        # ============================================================
        # DEBT-FREE BLUE CHIP
        # ============================================================

        if "debt_to_equity_max" in filters:

            result = self._apply_debt_to_equity_filter(
                result,
                filters["debt_to_equity_max"],
            )

        if "roe_min" in filters:

            result = result[
                result["return_on_equity_pct"]
                > filters["roe_min"]
            ]

        if "sales_min" in filters:

            result = result[
                result["sales"]
                > filters["sales_min"]
            ]

        # ============================================================
        # TURNAROUND WATCH
        # ============================================================

        if (
            "revenue_cagr_3yr_min" in filters
            or "debt_to_equity_declining" in filters
        ):

            historical_df = (
                self.load_historical_metrics()
            )

            turnaround_metrics = (
                self.calculate_turnaround_metrics(
                    historical_df
                )
            )

            result = result.merge(
                turnaround_metrics,
                on="company_id",
                how="left",
            )

        # Revenue CAGR > threshold

        if "revenue_cagr_3yr_min" in filters:

            result = result[
                result["revenue_cagr_3yr"]
                > filters["revenue_cagr_3yr_min"]
            ]

        # Latest FCF positive

        if "free_cash_flow_min" in filters:

            result = result[
                result["free_cash_flow_cr"]
                > filters["free_cash_flow_min"]
            ]

        # D/E declining YoY

        if filters.get(
            "debt_to_equity_declining"
        ) is True:

            result = result[
                result[
                    "debt_to_equity_declining"
                ]
                == True
            ]

        return result

    # ----------------------------------------------------------------
    # Composite score
    # ----------------------------------------------------------------

    def calculate_composite_score(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Placeholder for Day 17 composite quality score.

        Day 17 will implement:
        - profitability score
        - cash quality score
        - growth score
        - leverage score
        - winsorization
        - sector-relative scoring
        - final 0-100 composite score
        """

        result = df.copy()

        if (
            "composite_quality_score"
            not in result.columns
        ):
            result[
                "composite_quality_score"
            ] = pd.NA

        return result

    # ----------------------------------------------------------------
    # Run screener
    # ----------------------------------------------------------------

    def run(
        self,
        screener_name: str,
        sort_by: str = "composite_quality_score",
        ascending: bool = False,
    ) -> pd.DataFrame:
        """
        Run a configured screener.
        """

        universe = self.load_universe()

        result = self.apply_filters(
            universe,
            screener_name,
        )

        result = self.calculate_composite_score(
            result
        )

        if sort_by in result.columns:

            result = result.sort_values(
                by=sort_by,
                ascending=ascending,
                na_position="last",
            )

        result = result.reset_index(
            drop=True
        )

        return result

    # ----------------------------------------------------------------
    # Convenience method
    # ----------------------------------------------------------------

    def run_all(
        self,
    ) -> dict[str, pd.DataFrame]:
        """
        Run all configured screeners.

        Returns:
            Dictionary mapping screener name to result DataFrame.
        """

        results = {}

        for screener_name in (
            self.get_screener_names()
        ):

            results[screener_name] = self.run(
                screener_name
            )

        return results


# ====================================================================
# Direct execution
# ====================================================================

if __name__ == "__main__":

    engine = ScreenerEngine()

    print(
        "N100 Financial Intelligence Platform"
    )

    print(
        "Sprint 3 - Day 15 Screener Engine"
    )

    print("=" * 70)

    print()
    print("Configured Screeners:")
    print("-" * 70)

    for name in engine.get_screener_names():

        config = engine.get_screener_config(
            name
        )

        print(
            f"- {name}: "
            f"{config['name']}"
        )

    universe = engine.load_universe()

    print()
    print("Universe:")
    print("-" * 70)

    print(
        f"Companies: "
        f"{len(universe)}"
    )

    print(
        f"Unique companies: "
        f"{universe['company_id'].nunique()}"
    )

    print(
        f"Columns: "
        f"{len(universe.columns)}"
    )

    print()
    print("Screener Results:")
    print("-" * 70)

    for screener_name in (
        engine.get_screener_names()
    ):

        try:

            result = engine.run(
                screener_name
            )

            config = engine.get_screener_config(
                screener_name
            )

            print(
                f"{config['name']}: "
                f"{len(result)} companies"
            )

        except Exception as exc:

            print(
                f"{screener_name}: "
                f"ERROR - {exc}"
            )