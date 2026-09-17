"""
N100 Financial Intelligence Platform
Sprint 3 - Day 15
Screener Engine Core

Loads screener configuration from YAML, combines the required
financial tables, applies screener filters, and returns a
company-level screened DataFrame.

Day 15 capabilities:
- Latest-year company universe
- 15 filterable financial metrics
- Financial-sector D/E exemption
- Debt-Free ICR handling
- Config-driven screener filters
- Custom threshold filtering
- Existing composite quality score
- Composite-score sorting
- Turnaround Watch historical metrics
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
    # Day 15 - 15 filterable metrics
    # ----------------------------------------------------------------

    FILTER_COLUMN_MAP = {
        "roe_min": "return_on_equity_pct",
        "free_cash_flow_min": "free_cash_flow_cr",
        "revenue_cagr_5yr_min": "revenue_cagr_5yr",
        "pat_cagr_5yr_min": "pat_cagr_5yr",
        "opm_min": "operating_profit_margin_pct",
        "pe_max": "pe_ratio",
        "pb_max": "pb_ratio",
        "dividend_yield_min": "dividend_yield_pct",
        "icr_min": "effective_icr",
        "market_cap_min": "market_cap_crore",
        "net_profit_min": "net_profit",
        "eps_cagr_min": "eps_cagr_5yr",
        "asset_turnover_min": "asset_turnover",
        "sales_min": "sales",
    }

    # D/E is handled separately because Financials are exempt.
    DEBT_TO_EQUITY_FILTER = "debt_to_equity_max"

    # Special Turnaround Watch filters.
    SPECIAL_FILTERS = {
        "revenue_cagr_3yr_min",
        "debt_to_equity_declining",
    }

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

        Also creates:
        - effective_icr
        - debt_filter_allowed

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
            fr.icr_label,

            fr.asset_turnover,

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

            fr.composite_quality_score,

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

        # ------------------------------------------------------------
        # Effective ICR
        #
        # Debt-free companies receive infinity so that an ICR
        # threshold does not incorrectly reject them.
        # ------------------------------------------------------------

        df["effective_icr"] = pd.to_numeric(
            df["interest_coverage"],
            errors="coerce",
        )

        debt_free_mask = (
            df["icr_label"]
            .fillna("")
            .eq("Debt Free")
        )

        df.loc[
            debt_free_mask,
            "effective_icr",
        ] = float("inf")

        # ------------------------------------------------------------
        # Convert numeric columns to numeric dtype where possible.
        # ------------------------------------------------------------

        numeric_columns = [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "return_on_assets_pct",
            "debt_to_equity",
            "interest_coverage",
            "effective_icr",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "cash_from_operations_cr",
            "total_debt_cr",
            "net_debt",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "composite_quality_score",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
            "sales",
            "net_profit",
            "operating_profit",
            "pnl_eps",
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
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
                    "revenue_cagr_3yr":
                        revenue_cagr_3yr,
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

        return result.loc[final_mask].copy()

    # ----------------------------------------------------------------
    # Generic Day 15 filter engine
    # ----------------------------------------------------------------

    def apply_filter_config(
        self,
        df: pd.DataFrame,
        filters: dict,
    ) -> pd.DataFrame:
        """
        Apply a dictionary of financial screening thresholds.

        Supported Day 15 metrics:

        1.  roe_min
        2.  debt_to_equity_max
        3.  free_cash_flow_min
        4.  revenue_cagr_5yr_min
        5.  pat_cagr_5yr_min
        6.  opm_min
        7.  pe_max
        8.  pb_max
        9.  dividend_yield_min
        10. icr_min
        11. market_cap_min
        12. net_profit_min
        13. eps_cagr_min
        14. asset_turnover_min
        15. sales_min

        Special Turnaround Watch metrics are handled separately.
        """

        result = df.copy()

        # ------------------------------------------------------------
        # Validate filter names
        # ------------------------------------------------------------

        supported_filters = (
            set(self.FILTER_COLUMN_MAP.keys())
            | {self.DEBT_TO_EQUITY_FILTER}
            | self.SPECIAL_FILTERS
            | {"dividend_payout_ratio_max"}
        )

        unknown_filters = (
            set(filters.keys())
            - supported_filters
        )

        if unknown_filters:
            raise ValueError(
                "Unsupported screener filter(s): "
                f"{sorted(unknown_filters)}"
            )

        # ------------------------------------------------------------
        # Generic minimum filters
        # ------------------------------------------------------------

        minimum_filters = {
            key: value
            for key, value in filters.items()
            if key.endswith("_min")
            and key in self.FILTER_COLUMN_MAP
        }

        for filter_name, threshold in (
            minimum_filters.items()
        ):

            column = self.FILTER_COLUMN_MAP[
                filter_name
            ]

            if column not in result.columns:
                raise KeyError(
                    f"Required column '{column}' "
                    f"not found for filter "
                    f"'{filter_name}'."
                )

            result = result.loc[
                result[column] > threshold
            ].copy()

        # ------------------------------------------------------------
        # Maximum filters
        # ------------------------------------------------------------

        maximum_filters = {
            key: value
            for key, value in filters.items()
            if key.endswith("_max")
            and key in self.FILTER_COLUMN_MAP
        }

        for filter_name, threshold in (
            maximum_filters.items()
        ):

            column = self.FILTER_COLUMN_MAP[
                filter_name
            ]

            if column not in result.columns:
                raise KeyError(
                    f"Required column '{column}' "
                    f"not found for filter "
                    f"'{filter_name}'."
                )

            result = result.loc[
                result[column] < threshold
            ].copy()

        # ------------------------------------------------------------
        # Dividend payout maximum
        # ------------------------------------------------------------

        if "dividend_payout_ratio_max" in filters:

            column = "dividend_payout_ratio_pct"

            result = result.loc[
                result[column]
                < filters[
                    "dividend_payout_ratio_max"
                ]
            ].copy()

        # ------------------------------------------------------------
        # D/E filter
        #
        # Financials are exempt.
        # ------------------------------------------------------------

        if self.DEBT_TO_EQUITY_FILTER in filters:

            result = (
                self._apply_debt_to_equity_filter(
                    result,
                    filters[
                        self.DEBT_TO_EQUITY_FILTER
                    ],
                )
            )

        return result

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

        Standard financial filters are handled by the generic
        Day 15 filter engine.

        Turnaround Watch additionally calculates historical
        revenue CAGR and D/E trend.
        """

        config = self.get_screener_config(
            screener_name
        )

        filters = config.get(
            "filters",
            {},
        )

        result = self.apply_filter_config(
            df,
            filters,
        )
        # Debt-Free Blue Chip requires strict D/E = 0
        # for every company, including Financials.
        if (
            screener_name == "debt_free_blue_chip"
            and "debt_to_equity_max" in filters
            and filters["debt_to_equity_max"] == 0
        ):
            result = result[
                result["debt_to_equity"].fillna(float("inf")) == 0
            ].copy()

        # ------------------------------------------------------------
        # Turnaround Watch historical calculations
        # ------------------------------------------------------------

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

        # ------------------------------------------------------------
        # Revenue CAGR 3-year filter
        # ------------------------------------------------------------

        if "revenue_cagr_3yr_min" in filters:

            result = result.loc[
                result["revenue_cagr_3yr"]
                > filters[
                    "revenue_cagr_3yr_min"
                ]
            ].copy()

        # ------------------------------------------------------------
        # D/E declining YoY
        # ------------------------------------------------------------

        if filters.get(
            "debt_to_equity_declining"
        ) is True:

            result = result.loc[
                result[
                    "debt_to_equity_declining"
                ].eq(True)
            ].copy()

        return result

    # ----------------------------------------------------------------
    # Composite score
    # ----------------------------------------------------------------

    def calculate_composite_score(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Use the existing composite quality score stored in
        financial_ratios.

        Day 17 will replace/refine this with the complete
        0-100 scoring methodology:

        - profitability
        - cash quality
        - growth
        - leverage
        - winsorization
        - sector-relative scoring
        """

        result = df.copy()

        if "composite_quality_score" not in result.columns:
            raise KeyError(
                "composite_quality_score is missing "
                "from the screener universe."
            )

        result[
            "composite_quality_score"
        ] = pd.to_numeric(
            result[
                "composite_quality_score"
            ],
            errors="coerce",
        )

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

        Results are sorted by composite quality score
        descending by default.
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
    # Custom threshold screener
    # ----------------------------------------------------------------

    def run_custom(
        self,
        filters: dict,
        sort_by: str = "composite_quality_score",
        ascending: bool = False,
    ) -> pd.DataFrame:
        """
        Run a custom screener using user-supplied thresholds.

        Example:

            filters = {
                "roe_min": 15,
                "debt_to_equity_max": 1,
                "free_cash_flow_min": 0,
                "revenue_cagr_5yr_min": 10,
            }

            result = engine.run_custom(filters)
        """

        universe = self.load_universe()

        result = self.apply_filter_config(
            universe,
            filters,
        )

        # ------------------------------------------------------------
        # Custom Turnaround Watch support
        # ------------------------------------------------------------

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

        if "revenue_cagr_3yr_min" in filters:

            result = result.loc[
                result["revenue_cagr_3yr"]
                > filters[
                    "revenue_cagr_3yr_min"
                ]
            ].copy()

        if filters.get(
            "debt_to_equity_declining"
        ) is True:

            result = result.loc[
                result[
                    "debt_to_equity_declining"
                ].eq(True)
            ].copy()

        result = self.calculate_composite_score(
            result
        )

        if sort_by in result.columns:

            result = result.sort_values(
                by=sort_by,
                ascending=ascending,
                na_position="last",
            )

        return result.reset_index(
            drop=True
        )

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

    # ---------------------------------------------------------------
    # Universe
    # ---------------------------------------------------------------

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

    print(
        f"Debt Free ICR rows: "
        f"{(universe['icr_label'] == 'Debt Free').sum()}"
    )

    print(
        f"Composite scores available: "
        f"{universe['composite_quality_score'].notna().sum()}"
    )

    # ---------------------------------------------------------------
    # Screener results
    # ---------------------------------------------------------------

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

            sorted_status = (
                result[
                    "composite_quality_score"
                ]
                .is_monotonic_decreasing
            )

            print(
                f"{config['name']}: "
                f"{len(result)} companies | "
                f"sorted={sorted_status}"
            )

        except Exception as exc:

            print(
                f"{screener_name}: "
                f"ERROR - {exc}"
            )