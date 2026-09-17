"""
N100 Financial Intelligence Platform
Sprint 6 - Day 37
Cluster Profiling & Statistics

Tasks:
1. Profile all 5 KMeans clusters.
2. Compute mean and median of the 5 clustering features.
3. Assign descriptive cluster names based on financial profiles.
4. Generate Pearson correlation heatmap for 10 KPIs.
5. Detect sector-wise outliers using Z-score > 3.
6. Generate portfolio statistics:
   P10, P25, P50, P75, P90, Mean, Std.
"""

from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import zscore


warnings.filterwarnings("ignore")


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# ============================================================
# DATABASE IMPORTS
# ============================================================

from dashboard.utils.db import (
    get_companies,
    get_ratios,
)


# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FILE PATHS
# ============================================================

CLUSTER_LABELS_PATH = (
    OUTPUT_DIR / "cluster_labels.csv"
)

CORRELATION_HEATMAP_PATH = (
    REPORTS_DIR / "correlation_heatmap.png"
)

OUTLIER_REPORT_PATH = (
    OUTPUT_DIR / "outlier_report.csv"
)

PORTFOLIO_STATS_PATH = (
    OUTPUT_DIR / "portfolio_stats.csv"
)


# ============================================================
# REQUIRED CLUSTERING FEATURES
# ============================================================

CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


# ============================================================
# 10 KPI FEATURES FOR CORRELATION / STATISTICS
# ============================================================

KPI_COLUMNS = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "return_on_capital_employed_pct",
    "return_on_assets_pct",
    "interest_coverage",
    "asset_turnover",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def clean_numeric(df, columns):
    """
    Convert requested columns to numeric.
    """

    result = df.copy()

    for column in columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def find_column(df, candidates):
    """
    Return the first matching column.
    """

    for candidate in candidates:

        if candidate in df.columns:
            return candidate

    return None


def safe_ratio(ticker, year=None):
    """
    Safely retrieve ratio data.
    """

    try:

        result = get_ratios(
            str(ticker),
            year,
        )

        if result is None:
            return pd.DataFrame()

        return result.copy()

    except Exception:

        return pd.DataFrame()


# ============================================================
# CLUSTER NAME LOGIC
# ============================================================

def assign_cluster_names(cluster_profiles):
    """
    Assign descriptive names based on the actual financial
    characteristics of each cluster.

    The names are deliberately based on profile characteristics
    rather than assuming a fixed KMeans cluster ID.
    """

    names = {}

    for cluster_id, row in cluster_profiles.iterrows():

        roe = row["return_on_equity_pct_mean"]
        de = row["debt_to_equity_mean"]
        revenue_growth = row["revenue_cagr_5yr_mean"]
        fcf_growth = row["fcf_cagr_5yr_mean"]
        opm = row["operating_profit_margin_pct_mean"]

        # ----------------------------------------------------
        # High quality:
        # high ROE + high margin + healthy growth
        # ----------------------------------------------------

        if (
            roe >= 30
            and opm >= 30
            and revenue_growth >= 10
        ):

            names[cluster_id] = (
                "High-Quality Compounders"
            )

        # ----------------------------------------------------
        # Defensive:
        # strong profitability + low leverage
        # ----------------------------------------------------

        elif (
            de <= 0.5
            and roe >= 20
            and opm >= 20
        ):

            names[cluster_id] = (
                "Defensive Quality"
            )

        # ----------------------------------------------------
        # Emerging growth:
        # strong revenue / FCF growth
        # ----------------------------------------------------

        elif (
            revenue_growth >= 15
            or fcf_growth >= 25
        ):

            names[cluster_id] = (
                "Emerging Growth"
            )

        # ----------------------------------------------------
        # Distressed / turnaround:
        # relatively weak growth / profitability
        # or elevated leverage
        # ----------------------------------------------------

        elif (
            de >= 1.0
            or revenue_growth < 8
            or opm < 15
        ):

            names[cluster_id] = (
                "Distressed / Turnaround"
            )

        # ----------------------------------------------------
        # Remaining balanced cluster
        # ----------------------------------------------------

        else:

            names[cluster_id] = (
                "Value / Balanced"
            )

    return names


# ============================================================
# [1/8] LOAD CLUSTER LABELS
# ============================================================

section("[1/8] Loading Day 36 cluster labels")

if not CLUSTER_LABELS_PATH.exists():

    raise FileNotFoundError(
        f"Required file not found:\n"
        f"{CLUSTER_LABELS_PATH}\n\n"
        f"Run Day 36 clustering first."
    )


cluster_labels = pd.read_csv(
    CLUSTER_LABELS_PATH
)

print(
    f"Cluster label rows: {len(cluster_labels)}"
)

print(
    f"Unique companies: "
    f"{cluster_labels['company_id'].nunique()}"
)


# ============================================================
# NORMALIZE CLUSTER ID
# ============================================================

cluster_labels["cluster_id"] = pd.to_numeric(
    cluster_labels["cluster_id"],
    errors="coerce",
)

cluster_labels = cluster_labels.dropna(
    subset=["cluster_id"]
)

cluster_labels["cluster_id"] = (
    cluster_labels["cluster_id"]
    .astype(int)
)


# ============================================================
# [2/8] LOAD COMPANY MASTER
# ============================================================

section("[2/8] Loading company master")

companies = get_companies()

if companies is None:

    companies = pd.DataFrame()


print(
    f"Companies loaded: {len(companies)}"
)


# ============================================================
# IDENTIFY COMPANY ID / SECTOR
# ============================================================

company_id_column = find_column(
    companies,
    [
        "id",
        "company_id",
        "ticker",
        "nse_ticker",
    ],
)

sector_column = find_column(
    companies,
    [
        "broad_sector",
        "sector",
        "sector_name",
        "industry",
    ],
)


if company_id_column is None:

    raise ValueError(
        "Could not identify company ID column "
        "in company master."
    )


print(
    f"Company ID column: {company_id_column}"
)

print(
    f"Sector column: {sector_column}"
)


companies = companies.copy()

companies["company_id"] = (
    companies[company_id_column]
    .astype(str)
    .str.strip()
)


if sector_column is not None:

    companies["broad_sector"] = (
        companies[sector_column]
        .astype(str)
        .str.strip()
    )

else:

    companies["broad_sector"] = "Unknown"


# ============================================================
# MERGE COMPANY MASTER WITH CLUSTERS
# ============================================================

cluster_labels["company_id"] = (
    cluster_labels["company_id"]
    .astype(str)
    .str.strip()
)

cluster_data = cluster_labels.merge(
    companies[
        [
            "company_id",
            "broad_sector",
        ]
    ],
    on="company_id",
    how="left",
)


cluster_data["broad_sector"] = (
    cluster_data["broad_sector"]
    .fillna("Unknown")
)


# ============================================================
# [3/8] LOAD LATEST YEAR RATIOS
# ============================================================

section("[3/8] Loading latest-year financial ratios")

latest_year = 2024

if "year" in cluster_labels.columns:

    years = pd.to_numeric(
        cluster_labels["year"],
        errors="coerce",
    ).dropna()

    if not years.empty:

        latest_year = int(
            years.max()
        )


print(
    f"Latest financial year: {latest_year}"
)


ratio_frames = []

tickers = (
    companies["company_id"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)


for ticker in tickers:

    df = safe_ratio(
        ticker,
        latest_year,
    )

    if df.empty:
        continue

    df = df.copy()

    df["company_id"] = ticker

    ratio_frames.append(df)


if ratio_frames:

    ratios = pd.concat(
        ratio_frames,
        ignore_index=True,
    )

else:

    ratios = pd.DataFrame()


print(
    f"Ratio rows loaded: {len(ratios)}"
)

print(
    f"Unique ratio companies: "
    f"{ratios['company_id'].nunique() if not ratios.empty else 0}"
)


# ============================================================
# KEEP ONE LATEST ROW PER COMPANY
# ============================================================

if not ratios.empty:

    if "year" in ratios.columns:

        ratios["year"] = pd.to_numeric(
            ratios["year"],
            errors="coerce",
        )

        ratios = (
            ratios
            .sort_values("year")
            .groupby(
                "company_id",
                as_index=False,
            )
            .tail(1)
        )

    else:

        ratios = (
            ratios
            .groupby(
                "company_id",
                as_index=False,
            )
            .tail(1)
        )


# ============================================================
# NORMALIZE NUMERIC FEATURES
# ============================================================

ratios = clean_numeric(
    ratios,
    KPI_COLUMNS,
)


# ============================================================
# MERGE CLUSTERS + RATIOS
# ============================================================

analysis_df = cluster_data.merge(
    ratios[
        [
            "company_id"
        ]
        + [
            column
            for column in KPI_COLUMNS
            if column in ratios.columns
        ]
    ],
    on="company_id",
    how="left",
)


# ============================================================
# [4/8] CLUSTER PROFILING
# ============================================================

section("[4/8] Profiling five KMeans clusters")


profile_rows = []


for cluster_id in sorted(
    analysis_df["cluster_id"].unique()
):

    subset = analysis_df[
        analysis_df["cluster_id"]
        == cluster_id
    ]

    row = {
        "cluster_id": cluster_id,
        "company_count": len(subset),
    }


    for feature in CLUSTER_FEATURES:

        if feature not in subset.columns:

            row[
                f"{feature}_mean"
            ] = np.nan

            row[
                f"{feature}_median"
            ] = np.nan

            continue


        values = pd.to_numeric(
            subset[feature],
            errors="coerce",
        ).dropna()


        if values.empty:

            mean_value = np.nan
            median_value = np.nan

        else:

            mean_value = float(
                values.mean()
            )

            median_value = float(
                values.median()
            )


        row[
            f"{feature}_mean"
        ] = mean_value

        row[
            f"{feature}_median"
        ] = median_value


    profile_rows.append(row)


cluster_profiles = pd.DataFrame(
    profile_rows
)


# ============================================================
# ASSIGN DESCRIPTIVE NAMES
# ============================================================

cluster_name_map = assign_cluster_names(
    cluster_profiles.set_index(
        "cluster_id"
    )
)


cluster_profiles[
    "cluster_name"
] = cluster_profiles[
    "cluster_id"
].map(
    cluster_name_map
)


# ============================================================
# PRINT CLUSTER PROFILES
# ============================================================

print()

for _, row in cluster_profiles.iterrows():

    cluster_id = int(
        row["cluster_id"]
    )

    cluster_name = row[
        "cluster_name"
    ]

    company_count = int(
        row["company_count"]
    )

    print(
        f"Cluster {cluster_id}: "
        f"{cluster_name}"
    )

    print(
        f"Companies: {company_count}"
    )

    for feature in CLUSTER_FEATURES:

        mean_value = row[
            f"{feature}_mean"
        ]

        median_value = row[
            f"{feature}_median"
        ]

        print(
            f"  {feature}: "
            f"mean={mean_value:.2f} | "
            f"median={median_value:.2f}"
        )

    print()


# ============================================================
# UPDATE CLUSTER LABELS WITH FINAL NAMES
# ============================================================

cluster_labels[
    "cluster_name"
] = cluster_labels[
    "cluster_id"
].map(
    cluster_name_map
)


# ============================================================
# SAVE PROFILE REPORT
# ============================================================

cluster_profile_output = (
    OUTPUT_DIR
    / "cluster_profiles.csv"
)

cluster_profiles.to_csv(
    cluster_profile_output,
    index=False,
)

print(
    f"Cluster profile saved to:\n"
    f"{cluster_profile_output}"
)


# ============================================================
# [5/8] CORRELATION MATRIX
# ============================================================

section(
    "[5/8] Generating 10-KPI Pearson correlation heatmap"
)


available_kpis = [
    column
    for column in KPI_COLUMNS
    if column in analysis_df.columns
]


correlation_data = analysis_df[
    available_kpis
].copy()


correlation_data = clean_numeric(
    correlation_data,
    available_kpis,
)


correlation_matrix = (
    correlation_data
    .corr(
        method="pearson"
    )
)


print(
    f"KPIs included: "
    f"{len(available_kpis)}"
)

print(
    correlation_matrix.round(3)
)


# ============================================================
# HEATMAP
# ============================================================

plt.figure(
    figsize=(14, 10)
)


sns.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5,
    square=True,
    cbar_kws={
        "label": "Pearson Correlation"
    },
)


plt.title(
    "N100 Financial KPI Correlation Matrix",
    fontsize=16,
    fontweight="bold",
    pad=15,
)


plt.xticks(
    rotation=45,
    ha="right",
)


plt.yticks(
    rotation=0,
)


plt.tight_layout()


plt.savefig(
    CORRELATION_HEATMAP_PATH,
    dpi=200,
    bbox_inches="tight",
)


plt.close()


print(
    f"Correlation heatmap saved to:\n"
    f"{CORRELATION_HEATMAP_PATH}"
)


# ============================================================
# [6/8] SECTOR-WISE OUTLIER DETECTION
# ============================================================

section(
    "[6/8] Detecting sector-wise KPI outliers"
)


outlier_base = analysis_df.copy()


outlier_rows = []


for sector_name, sector_df in (
    outlier_base
    .groupby("broad_sector")
):

    sector_df = sector_df.copy()


    for metric in KPI_COLUMNS:

        if metric not in sector_df.columns:
            continue


        values = pd.to_numeric(
            sector_df[metric],
            errors="coerce",
        )


        valid_values = values.dropna()


        # ----------------------------------------------------
        # Z-score requires at least two observations
        # and non-zero standard deviation.
        # ----------------------------------------------------

        if (
            len(valid_values) < 2
            or valid_values.std(
                ddof=0
            ) == 0
        ):

            continue


        z_scores = (
            values
            - valid_values.mean()
        ) / valid_values.std(
            ddof=0
        )


        for idx, z_value in (
            z_scores.items()
        ):

            if pd.isna(z_value):
                continue


            if abs(z_value) > 3:

                company_id = (
                    sector_df
                    .loc[
                        idx,
                        "company_id",
                    ]
                )


                company_name = (
                    sector_df
                    .loc[
                        idx,
                        "company_id",
                    ]
                )


                if (
                    "company_name"
                    in sector_df.columns
                ):

                    company_name = (
                        sector_df
                        .loc[
                            idx,
                            "company_name",
                        ]
                    )


                cluster_id = (
                    sector_df
                    .loc[
                        idx,
                        "cluster_id",
                    ]
                )


                cluster_name = (
                    sector_df
                    .loc[
                        idx,
                        "cluster_name",
                    ]
                    if "cluster_name"
                    in sector_df.columns
                    else cluster_name_map.get(
                        cluster_id,
                        "Unknown",
                    )
                )


                outlier_rows.append(
                    {
                        "company_id":
                            company_id,

                        "company_name":
                            company_name,

                        "broad_sector":
                            sector_name,

                        "cluster_id":
                            cluster_id,

                        "cluster_name":
                            cluster_name,

                        "metric":
                            metric,

                        "metric_value":
                            float(
                                values.loc[idx]
                            ),

                        "sector_mean":
                            float(
                                valid_values.mean()
                            ),

                        "sector_std":
                            float(
                                valid_values.std(
                                    ddof=0
                                )
                            ),

                        "z_score":
                            float(
                                z_value
                            ),

                        "absolute_z_score":
                            float(
                                abs(z_value)
                            ),

                        "outlier_flag":
                            "OUTLIER",
                    }
                )


# ============================================================
# OUTLIER DATAFRAME
# ============================================================

outlier_report = pd.DataFrame(
    outlier_rows
)


if not outlier_report.empty:

    outlier_report = (
        outlier_report
        .sort_values(
            [
                "broad_sector",
                "absolute_z_score",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )


else:

    outlier_report = pd.DataFrame(
        columns=[
            "company_id",
            "company_name",
            "broad_sector",
            "cluster_id",
            "cluster_name",
            "metric",
            "metric_value",
            "sector_mean",
            "sector_std",
            "z_score",
            "absolute_z_score",
            "outlier_flag",
        ]
    )


outlier_report.to_csv(
    OUTLIER_REPORT_PATH,
    index=False,
)


print(
    f"Outlier observations: "
    f"{len(outlier_report)}"
)

print(
    f"Outlier report saved to:\n"
    f"{OUTLIER_REPORT_PATH}"
)


# ============================================================
# [7/8] PORTFOLIO STATISTICS
# ============================================================

section(
    "[7/8] Generating portfolio statistics"
)


statistics_rows = []


for metric in KPI_COLUMNS:

    if metric not in analysis_df.columns:
        continue


    values = pd.to_numeric(
        analysis_df[metric],
        errors="coerce",
    ).dropna()


    if values.empty:

        statistics_rows.append(
            {
                "kpi": metric,
                "count": 0,
                "p10": np.nan,
                "p25": np.nan,
                "p50": np.nan,
                "p75": np.nan,
                "p90": np.nan,
                "mean": np.nan,
                "std": np.nan,
            }
        )

        continue


    statistics_rows.append(
        {
            "kpi": metric,

            "count":
                int(values.count()),

            "p10":
                float(
                    values.quantile(
                        0.10
                    )
                ),

            "p25":
                float(
                    values.quantile(
                        0.25
                    )
                ),

            "p50":
                float(
                    values.quantile(
                        0.50
                    )
                ),

            "p75":
                float(
                    values.quantile(
                        0.75
                    )
                ),

            "p90":
                float(
                    values.quantile(
                        0.90
                    )
                ),

            "mean":
                float(
                    values.mean()
                ),

            "std":
                float(
                    values.std(
                        ddof=1
                    )
                ),
        }
    )


portfolio_stats = pd.DataFrame(
    statistics_rows
)


portfolio_stats.to_csv(
    PORTFOLIO_STATS_PATH,
    index=False,
)


print(
    portfolio_stats.to_string(
        index=False
    )
)


print(
    f"\nPortfolio statistics saved to:\n"
    f"{PORTFOLIO_STATS_PATH}"
)


# ============================================================
# [8/8] FINAL VALIDATION
# ============================================================

section(
    "[8/8] Day 37 final validation"
)


expected_companies = 92

cluster_company_count = (
    cluster_labels[
        "company_id"
    ].nunique()
)


cluster_count = (
    cluster_labels[
        "cluster_id"
    ].nunique()
)


print(
    f"Companies expected       : "
    f"{expected_companies}"
)

print(
    f"Companies in clusters    : "
    f"{cluster_company_count}"
)

print(
    f"Unique clusters          : "
    f"{cluster_count}"
)

print(
    f"Correlation heatmap      : "
    f"{CORRELATION_HEATMAP_PATH.exists()}"
)

print(
    f"Outlier report           : "
    f"{OUTLIER_REPORT_PATH.exists()}"
)

print(
    f"Portfolio statistics     : "
    f"{PORTFOLIO_STATS_PATH.exists()}"
)


# ============================================================
# CLUSTER DISTRIBUTION
# ============================================================

print()
print("Cluster distribution:")

distribution = (
    cluster_labels
    .groupby(
        [
            "cluster_id",
            "cluster_name",
        ]
    )
    .size()
    .reset_index(
        name="companies"
    )
)


print(
    distribution.to_string(
        index=False
    )
)


# ============================================================
# REQUIRED COLUMN VALIDATION
# ============================================================

required_cluster_columns = [
    "company_id",
    "cluster_id",
    "cluster_name",
]


required_outlier_columns = [
    "company_id",
    "broad_sector",
    "metric",
    "metric_value",
    "z_score",
    "absolute_z_score",
]


required_stats_columns = [
    "kpi",
    "p10",
    "p25",
    "p50",
    "p75",
    "p90",
    "mean",
    "std",
]


cluster_columns_ok = all(
    column in cluster_labels.columns
    for column in required_cluster_columns
)


outlier_columns_ok = all(
    column in outlier_report.columns
    for column in required_outlier_columns
)


stats_columns_ok = all(
    column in portfolio_stats.columns
    for column in required_stats_columns
)


# ============================================================
# FINAL PASS / FAIL
# ============================================================

all_checks = [
    cluster_company_count == expected_companies,
    cluster_count == 5,
    CORRELATION_HEATMAP_PATH.exists(),
    OUTLIER_REPORT_PATH.exists(),
    PORTFOLIO_STATS_PATH.exists(),
    cluster_columns_ok,
    outlier_columns_ok,
    stats_columns_ok,
]


if all(all_checks):

    print()
    print(
        "=" * 72
    )

    print(
        "DAY 37 CLUSTER PROFILING & "
        "STATISTICS: PASS"
    )

    print(
        "=" * 72
    )


else:

    print()
    print(
        "=" * 72
    )

    print(
        "DAY 37 CLUSTER PROFILING & "
        "STATISTICS: REVIEW REQUIRED"
    )

    print(
        "=" * 72
    )