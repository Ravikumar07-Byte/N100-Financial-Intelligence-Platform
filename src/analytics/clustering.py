"""
N100 Financial Intelligence Platform
Sprint 6 - Day 36
KMeans Financial Clustering

Purpose
-------
Cluster all N100 companies into 5 financial archetypes using:

1. return_on_equity_pct
2. debt_to_equity
3. revenue_cagr_5yr
4. fcf_cagr_5yr
5. operating_profit_margin_pct

Processing
----------
1. Load all companies and historical financial ratios.
2. Determine the latest available financial year.
3. Calculate 5-year FCF CAGR from free_cash_flow_cr.
4. Build the latest-year company feature dataset.
5. Impute missing feature values using sector medians.
6. Standardize features using StandardScaler.
7. Run KMeans with 5 clusters and random_state=42.
8. Calculate distance from each company to its centroid.
9. Generate elbow plot for k=2 through k=10.
10. Generate cluster_labels.csv.

Outputs
-------
reports/elbow_plot.png

output/cluster_labels.csv

The CSV contains:
    company_id
    cluster_id
    cluster_name
    distance_from_centroid
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

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
    get_all_ratios,
    get_companies,
)

# ============================================================
# CONFIGURATION
# ============================================================

N_CLUSTERS = 5

RANDOM_STATE = 42

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLUSTER_OUTPUT = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_OUTPUT = REPORTS_DIR / "elbow_plot.png"


# ============================================================
# DIRECTORY SETUP
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LOGGING HELPERS
# ============================================================


def print_section(title):
    """Print a readable terminal section."""

    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# NUMERIC CLEANING
# ============================================================


def convert_numeric(df, columns):
    """
    Convert selected columns to numeric.

    Invalid values become NaN.
    """

    result = df.copy()

    for column in columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


# ============================================================
# YEAR NORMALISATION
# ============================================================


def year_number(value):
    """
    Convert database year values such as:

        2024
        2024-03
        2024/03

    into integer 2024.
    """

    if pd.isna(value):
        return None

    text = str(value).strip()

    if len(text) >= 4:

        try:
            return int(text[:4])

        except ValueError:
            return None

    try:
        return int(text)

    except ValueError:
        return None


# ============================================================
# FCF CAGR CALCULATION
# ============================================================


def calculate_fcf_cagr(history):
    """
    Calculate 5-year FCF CAGR.

    Formula:

        CAGR =
        ((Ending FCF / Beginning FCF) ** (1 / 5) - 1) * 100

    A valid CAGR requires:

        - at least two observations
        - approximately a five-year interval
        - positive beginning FCF
        - positive ending FCF

    If these conditions are not satisfied, NaN is returned.

    Negative or zero FCF cannot be used directly in the
    standard CAGR formula, so those cases are left missing
    and later handled through sector-median imputation.
    """

    if history is None or history.empty:
        return float("nan")

    required = {
        "year",
        "free_cash_flow_cr",
    }

    if not required.issubset(history.columns):
        return float("nan")

    df = history[
        [
            "year",
            "free_cash_flow_cr",
        ]
    ].copy()

    df["year_num"] = df["year"].apply(year_number)

    df["free_cash_flow_cr"] = pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "year_num",
            "free_cash_flow_cr",
        ]
    )

    if df.empty:
        return float("nan")

    df = df.sort_values("year_num").drop_duplicates(
        subset=["year_num"],
        keep="last",
    )

    latest_year = int(df["year_num"].max())

    target_start_year = latest_year - 5

    # --------------------------------------------------------
    # Prefer an observation exactly five years earlier.
    # --------------------------------------------------------

    exact_start = df[df["year_num"] == target_start_year]

    if not exact_start.empty:

        start_value = float(exact_start.iloc[-1]["free_cash_flow_cr"])

        end_rows = df[df["year_num"] == latest_year]

        if not end_rows.empty:

            end_value = float(end_rows.iloc[-1]["free_cash_flow_cr"])

            if start_value > 0 and end_value > 0:

                return ((end_value / start_value) ** (1 / 5) - 1) * 100

    # --------------------------------------------------------
    # If exact five-year data is unavailable, find the
    # closest valid pair spanning at least five years.
    # --------------------------------------------------------

    candidates = []

    for _, start_row in df.iterrows():

        for _, end_row in df.iterrows():

            start_year = int(start_row["year_num"])

            end_year = int(end_row["year_num"])

            span = end_year - start_year

            start_value = float(start_row["free_cash_flow_cr"])

            end_value = float(end_row["free_cash_flow_cr"])

            if span >= 5 and start_value > 0 and end_value > 0:

                candidates.append(
                    (
                        abs(span - 5),
                        -end_year,
                        start_year,
                        end_year,
                        start_value,
                        end_value,
                    )
                )

    if not candidates:
        return float("nan")

    candidates.sort()

    (
        _,
        _,
        start_year,
        end_year,
        start_value,
        end_value,
    ) = candidates[0]

    span = end_year - start_year

    if span <= 0:
        return float("nan")

    return ((end_value / start_value) ** (1 / span) - 1) * 100


# ============================================================
# BUILD FCF CAGR TABLE
# ============================================================


def build_fcf_cagr_table(ratios):
    """
    Calculate one FCF CAGR value for every company.
    """

    rows = []

    if ratios.empty:
        return pd.DataFrame(
            columns=[
                "company_id",
                "fcf_cagr_5yr",
            ]
        )

    if "company_id" not in ratios.columns:
        return pd.DataFrame(
            columns=[
                "company_id",
                "fcf_cagr_5yr",
            ]
        )

    for company_id, group in ratios.groupby("company_id"):

        cagr = calculate_fcf_cagr(group)

        rows.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# LOAD COMPANY MASTER
# ============================================================

print_section("[1/8] Loading company master")

companies = get_companies()

if companies is None:
    companies = pd.DataFrame()

if companies.empty:
    raise RuntimeError("Company master is empty.")

if "id" not in companies.columns:
    raise RuntimeError("Company master does not contain the 'id' column.")


# ------------------------------------------------------------
# Rename company ID to common name.
# ------------------------------------------------------------

companies = companies.rename(
    columns={
        "id": "company_id",
    }
)


print(f"Companies loaded: {len(companies)}")

print(f"Unique companies: " f"{companies['company_id'].nunique()}")


# ============================================================
# IDENTIFY SECTOR COLUMN
# ============================================================

sector_candidates = [
    "broad_sector",
    "sector",
    "sector_name",
]

sector_column = None

for candidate in sector_candidates:

    if candidate in companies.columns:

        sector_column = candidate
        break


if sector_column is None:

    print("WARNING: No sector column found " "in company master.")

    companies["broad_sector"] = "Unknown"

else:

    if sector_column != "broad_sector":

        companies = companies.rename(columns={sector_column: "broad_sector"})


companies["company_id"] = companies["company_id"].astype(str).str.strip()

companies["broad_sector"] = (
    companies["broad_sector"].fillna("Unknown").astype(str).str.strip()
)

companies.loc[
    companies["broad_sector"] == "",
    "broad_sector",
] = "Unknown"


# ============================================================
# LOAD ALL HISTORICAL RATIOS
# ============================================================

print_section("[2/8] Loading historical financial ratios")

ratios = get_all_ratios()

if ratios is None:
    ratios = pd.DataFrame()

if ratios.empty:
    raise RuntimeError("No financial ratio data was returned.")

print(f"Total ratio rows: {len(ratios)}")

print(f"Unique ratio companies: " f"{ratios['company_id'].nunique()}")


# ============================================================
# NORMALISE RATIO DATA
# ============================================================

required_ratio_columns = [
    "company_id",
    "year",
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "operating_profit_margin_pct",
    "free_cash_flow_cr",
]

missing_ratio_columns = [
    column for column in required_ratio_columns if column not in ratios.columns
]

if missing_ratio_columns:

    raise RuntimeError(
        "Required ratio columns are missing:\n"
        + "\n".join(f"  - {column}" for column in missing_ratio_columns)
    )


ratios["company_id"] = ratios["company_id"].astype(str).str.strip()

ratios = convert_numeric(
    ratios,
    [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "operating_profit_margin_pct",
        "free_cash_flow_cr",
    ],
)

ratios["year_num"] = ratios["year"].apply(year_number)


# ============================================================
# DETERMINE LATEST YEAR
# ============================================================

valid_years = ratios["year_num"].dropna().astype(int)

if valid_years.empty:

    raise RuntimeError("Unable to determine financial year " "from ratio data.")

latest_year = int(valid_years.max())

print(f"Latest financial year: {latest_year}")


# ============================================================
# BUILD FCF CAGR
# ============================================================

print_section("[3/8] Calculating 5-year FCF CAGR")

fcf_cagr = build_fcf_cagr_table(ratios)

print(f"FCF CAGR values calculated: " f"{fcf_cagr['fcf_cagr_5yr'].notna().sum()}")

print(f"FCF CAGR unavailable: " f"{fcf_cagr['fcf_cagr_5yr'].isna().sum()}")


# ============================================================
# LATEST YEAR DATA
# ============================================================

print_section("[4/8] Building latest-year clustering dataset")

latest_ratios = ratios[ratios["year_num"] == latest_year].copy()


# ------------------------------------------------------------
# If multiple records exist for a company/year, retain one.
# ------------------------------------------------------------

latest_ratios = latest_ratios.sort_values(
    [
        "company_id",
        "year_num",
    ]
).drop_duplicates(
    subset=["company_id"],
    keep="last",
)


latest_features = latest_ratios[
    [
        "company_id",
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "operating_profit_margin_pct",
    ]
].copy()


# ============================================================
# MERGE COMPANY MASTER
# ============================================================

dataset = companies[
    [
        "company_id",
        "company_name",
        "broad_sector",
    ]
].copy()


dataset = dataset.merge(
    latest_features,
    on="company_id",
    how="left",
)


dataset = dataset.merge(
    fcf_cagr,
    on="company_id",
    how="left",
)


# ============================================================
# NORMALISE FEATURE DATA
# ============================================================

dataset = convert_numeric(
    dataset,
    FEATURES,
)


# ============================================================
# COVERAGE REPORT
# ============================================================

print(f"Companies in clustering dataset: " f"{len(dataset)}")

print(
    f"Companies with latest-year ratio row: "
    f"{latest_features['company_id'].nunique()}"
)


# ============================================================
# MISSING VALUE REPORT BEFORE IMPUTATION
# ============================================================

print()
print("Missing values before sector imputation:")
print("-" * 72)

for feature in FEATURES:

    missing = int(dataset[feature].isna().sum())

    print(f"{feature:<38} {missing:>3}")


# ============================================================
# SECTOR MEDIAN IMPUTATION
# ============================================================

print_section("[5/8] Imputing missing values with sector medians")

for feature in FEATURES:

    # --------------------------------------------------------
    # Calculate sector median using available values.
    # --------------------------------------------------------

    sector_medians = dataset.groupby("broad_sector")[feature].transform("median")

    # --------------------------------------------------------
    # First fill with sector median.
    # --------------------------------------------------------

    dataset[feature] = dataset[feature].fillna(sector_medians)

    # --------------------------------------------------------
    # If an entire sector has no value for the feature,
    # use the global median.
    # --------------------------------------------------------

    global_median = dataset[feature].median()

    if pd.isna(global_median):

        global_median = 0.0

    dataset[feature] = dataset[feature].fillna(global_median)


# ============================================================
# VERIFY NO MISSING VALUES
# ============================================================

print()
print("Missing values after imputation:")
print("-" * 72)

for feature in FEATURES:

    missing = int(dataset[feature].isna().sum())

    print(f"{feature:<38} {missing:>3}")


remaining_missing = int(dataset[FEATURES].isna().sum().sum())

if remaining_missing > 0:

    raise RuntimeError("Missing values remain after " "sector-median imputation.")


# ============================================================
# STANDARD SCALING
# ============================================================

print_section("[6/8] Standardizing clustering features")

X = dataset[FEATURES].copy()


scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


scaled_df = pd.DataFrame(
    X_scaled,
    columns=FEATURES,
    index=dataset.index,
)


print("StandardScaler applied.")

print("Feature means after scaling:")

print(scaled_df.mean().round(6).to_string())

print()
print("Feature standard deviations after scaling:")

print(scaled_df.std(ddof=0).round(6).to_string())


# ============================================================
# ELBOW ANALYSIS
# ============================================================

print_section("[7/8] Generating KMeans elbow plot")

inertias = []

k_values = list(
    range(
        2,
        11,
    )
)


for k in k_values:

    model = KMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    model.fit(X_scaled)

    inertias.append(model.inertia_)

    print(f"k={k:<2} " f"inertia={model.inertia_:,.4f}")


# ============================================================
# SAVE ELBOW PLOT
# ============================================================

plt.figure(figsize=(9, 6))

plt.plot(
    k_values,
    inertias,
    marker="o",
    linewidth=2,
)

plt.axvline(
    N_CLUSTERS,
    linestyle="--",
    linewidth=1.5,
    label="Selected k = 5",
)

plt.title("KMeans Elbow Analysis - N100 Financial Intelligence")

plt.xlabel("Number of Clusters (k)")

plt.ylabel("Inertia")

plt.xticks(k_values)

plt.grid(
    True,
    alpha=0.25,
)

plt.legend()

plt.tight_layout()

plt.savefig(
    ELBOW_OUTPUT,
    dpi=160,
    bbox_inches="tight",
)

plt.close()


print()
print(f"Elbow plot saved to:\n" f"{ELBOW_OUTPUT}")


# ============================================================
# FINAL KMEANS MODEL
# ============================================================

print()
print("Running final KMeans model:")

print(f"n_clusters = {N_CLUSTERS}")

print(f"random_state = {RANDOM_STATE}")


kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=RANDOM_STATE,
    n_init=20,
)

cluster_ids = kmeans.fit_predict(X_scaled)


# ============================================================
# DISTANCE FROM CENTROID
# ============================================================

all_distances = kmeans.transform(X_scaled)

distance_from_centroid = all_distances[
    range(len(dataset)),
    cluster_ids,
]


# ============================================================
# CLUSTER PROFILE
# ============================================================

cluster_profile = dataset[FEATURES].copy()

cluster_profile["cluster_id"] = cluster_ids


cluster_means = cluster_profile.groupby("cluster_id")[FEATURES].mean()


# ============================================================
# CLUSTER NAMING
# ============================================================


def assign_cluster_names(profile):
    """
    Assign deterministic descriptive names.

    Naming is based on the relative financial profile
    of each cluster.

    The five names are:

        High-Quality Compounders
        Defensive Quality
        Emerging Growth
        Value / Balanced
        Distressed / Turnaround

    The mapping is determined from the actual cluster
    statistics rather than hard-coding a specific cluster ID.
    """

    scores = pd.DataFrame(index=profile.index)

    # --------------------------------------------------------
    # Convert each metric to a rank.
    # Higher ROE / OPM / growth = better.
    # Lower D/E = better.
    # --------------------------------------------------------

    scores["quality"] = (
        profile["return_on_equity_pct"].rank(pct=True)
        + profile["operating_profit_margin_pct"].rank(pct=True)
        + profile["revenue_cagr_5yr"].rank(pct=True)
        + profile["fcf_cagr_5yr"].rank(pct=True)
        + (1 - profile["debt_to_equity"].rank(pct=True))
    )

    # --------------------------------------------------------
    # Growth score.
    # --------------------------------------------------------

    scores["growth"] = profile["revenue_cagr_5yr"].rank(pct=True) + profile[
        "fcf_cagr_5yr"
    ].rank(pct=True)

    # --------------------------------------------------------
    # Defensive score.
    # --------------------------------------------------------

    scores["defensive"] = (
        profile["return_on_equity_pct"].rank(pct=True)
        + profile["operating_profit_margin_pct"].rank(pct=True)
        + (1 - profile["debt_to_equity"].rank(pct=True))
    )

    # --------------------------------------------------------
    # Risk score.
    # Higher debt + weak profitability/growth.
    # --------------------------------------------------------

    scores["risk"] = (
        profile["debt_to_equity"].rank(pct=True)
        + (1 - profile["return_on_equity_pct"].rank(pct=True))
        + (1 - profile["operating_profit_margin_pct"].rank(pct=True))
        + (1 - profile["revenue_cagr_5yr"].rank(pct=True))
    )

    names = {}

    remaining = set(profile.index.tolist())

    # --------------------------------------------------------
    # 1. Distressed / Turnaround
    # --------------------------------------------------------

    distressed = int(
        scores.loc[
            list(remaining),
            "risk",
        ].idxmax()
    )

    names[distressed] = "Distressed / Turnaround"

    remaining.remove(distressed)

    # --------------------------------------------------------
    # 2. High-Quality Compounders
    # --------------------------------------------------------

    high_quality = int(
        scores.loc[
            list(remaining),
            "quality",
        ].idxmax()
    )

    names[high_quality] = "High-Quality Compounders"

    remaining.remove(high_quality)

    # --------------------------------------------------------
    # 3. Emerging Growth
    # --------------------------------------------------------

    emerging_growth = int(
        scores.loc[
            list(remaining),
            "growth",
        ].idxmax()
    )

    names[emerging_growth] = "Emerging Growth"

    remaining.remove(emerging_growth)

    # --------------------------------------------------------
    # 4. Defensive Quality
    # --------------------------------------------------------

    defensive = int(
        scores.loc[
            list(remaining),
            "defensive",
        ].idxmax()
    )

    names[defensive] = "Defensive Quality"

    remaining.remove(defensive)

    # --------------------------------------------------------
    # 5. Remaining cluster
    # --------------------------------------------------------

    for cluster_id in remaining:

        names[int(cluster_id)] = "Value / Balanced"

    return names


cluster_names = assign_cluster_names(cluster_means)


# ============================================================
# BUILD FINAL OUTPUT
# ============================================================

results = dataset[
    [
        "company_id",
    ]
].copy()


results["cluster_id"] = cluster_ids.astype(int)

results["cluster_name"] = results["cluster_id"].map(cluster_names)

results["distance_from_centroid"] = distance_from_centroid


# ============================================================
# ROUND DISTANCE
# ============================================================

results["distance_from_centroid"] = results["distance_from_centroid"].round(6)


# ============================================================
# SORT OUTPUT
# ============================================================

results = results.sort_values(
    [
        "cluster_id",
        "distance_from_centroid",
        "company_id",
    ]
).reset_index(drop=True)


# ============================================================
# VALIDATION
# ============================================================

print_section("[8/8] Validating clustering output")

print(f"Output companies: {len(results)}")

print(f"Unique companies: " f"{results['company_id'].nunique()}")

print(f"Cluster IDs: " f"{sorted(results['cluster_id'].unique())}")


# ------------------------------------------------------------
# Check company count.
# ------------------------------------------------------------

if len(results) != len(companies):

    raise RuntimeError("Clustering output does not contain " "all companies.")


# ------------------------------------------------------------
# Check duplicate companies.
# ------------------------------------------------------------

duplicate_count = int(results["company_id"].duplicated().sum())

if duplicate_count > 0:

    raise RuntimeError(f"Found {duplicate_count} " "duplicate company IDs.")


# ------------------------------------------------------------
# Check cluster IDs.
# ------------------------------------------------------------

valid_cluster_ids = set(range(N_CLUSTERS))

actual_cluster_ids = set(results["cluster_id"].unique())

if not actual_cluster_ids.issubset(valid_cluster_ids):

    raise RuntimeError("Invalid cluster IDs detected.")


# ------------------------------------------------------------
# Check cluster names.
# ------------------------------------------------------------

if results["cluster_name"].isna().any():

    raise RuntimeError("Some companies have no cluster name.")


# ------------------------------------------------------------
# Check distances.
# ------------------------------------------------------------

if results["distance_from_centroid"].isna().any():

    raise RuntimeError("Some companies have no " "centroid distance.")


# ============================================================
# SAVE CSV
# ============================================================

results.to_csv(
    CLUSTER_OUTPUT,
    index=False,
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("Cluster distribution:")

print(results["cluster_name"].value_counts().to_string())


print()
print("Cluster ID mapping:")

for cluster_id in sorted(cluster_names):

    print(f"  Cluster {cluster_id}: " f"{cluster_names[cluster_id]}")


print()
print("Cluster profile means:")

profile_display = cluster_means.copy().round(2)

profile_display["cluster_name"] = profile_display.index.map(cluster_names)

print(
    profile_display[
        [
            "cluster_name",
            *FEATURES,
        ]
    ].to_string()
)


print()
print("Final validation:")

print(f"  Companies expected : {len(companies)}")

print(f"  Companies clustered : {len(results)}")

print(f"  Unique companies    : " f"{results['company_id'].nunique()}")

print(f"  Number of clusters  : " f"{results['cluster_id'].nunique()}")

print(f"  Random state        : " f"{RANDOM_STATE}")

print(f"  Output CSV          : " f"{CLUSTER_OUTPUT}")

print(f"  Elbow plot          : " f"{ELBOW_OUTPUT}")


if (
    len(results) == len(companies)
    and results["company_id"].nunique() == len(companies)
    and results["cluster_id"].nunique() == N_CLUSTERS
):

    print()
    print("=" * 72)

    print("DAY 36 KMEANS CLUSTERING: PASS")

    print("=" * 72)

else:

    print()
    print("=" * 72)

    print("DAY 36 KMEANS CLUSTERING: REVIEW REQUIRED")

    print("=" * 72)
