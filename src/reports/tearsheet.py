"""
N100 Financial Intelligence Platform
Sprint 5 - Day 33
Company PDF Tearsheet Template

Creates a professional 2-page company financial tearsheet
using ReportLab and Matplotlib.

Page 1:
- Company header
- 6 KPI tiles
- 10-year Revenue and Net Profit charts
- ROE / ROCE dual-axis line chart

Page 2:
- Balance Sheet composition stacked bar
- Cash Flow waterfall
- Pros
- Cons
- Capital Allocation badge

Test companies:
TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL
"""

from __future__ import annotations

import math
import sqlite3
import re
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase.pdfmetrics import stringWidth


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "tearsheets"

PROS_CONS_FILE = (
    PROJECT_ROOT / "output" / "pros_cons_generated.csv"
)

CASHFLOW_INTELLIGENCE_FILE = (
    PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"
)

CHART_DIR = (
    PROJECT_ROOT / "output" / "_tearsheet_charts"
)


# ============================================================
# TEST COMPANIES
# ============================================================

TEST_COMPANIES = [
    "TCS",
    "HDFCBANK",
    "RELIANCE",
    "SUNPHARMA",
    "TATASTEEL",
]


# ============================================================
# DESIGN
# ============================================================

NAVY = colors.HexColor("#0B1736")
BLUE = colors.HexColor("#2563EB")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
GREEN = colors.HexColor("#16A34A")
LIGHT_GREEN = colors.HexColor("#F0FDF4")
RED = colors.HexColor("#DC2626")
LIGHT_RED = colors.HexColor("#FEF2F2")
GRAY = colors.HexColor("#64748B")
LIGHT_GRAY = colors.HexColor("#F1F5F9")
MID_GRAY = colors.HexColor("#CBD5E1")
DARK = colors.HexColor("#111827")
WHITE = colors.white


PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 12 * mm
RIGHT_MARGIN = 12 * mm
TOP_MARGIN = 12 * mm
BOTTOM_MARGIN = 12 * mm

CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


# ============================================================
# REPORTLAB STYLES
# ============================================================

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TearsheetTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=WHITE,
    alignment=TA_LEFT,
    spaceAfter=0,
)

SUBTITLE_STYLE = ParagraphStyle(
    "TearsheetSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#D7E3FF"),
)

SECTION_STYLE = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=NAVY,
    spaceBefore=2,
    spaceAfter=5,
)

NORMAL_STYLE = ParagraphStyle(
    "NormalTearsheet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=DARK,
)

SMALL_STYLE = ParagraphStyle(
    "SmallTearsheet",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=6.5,
    leading=8,
    textColor=GRAY,
)

PRO_STYLE = ParagraphStyle(
    "Pro",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.2,
    leading=9,
    textColor=colors.HexColor("#166534"),
)

CON_STYLE = ParagraphStyle(
    "Con",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.2,
    leading=9,
    textColor=colors.HexColor("#991B1B"),
)


# ============================================================
# DATABASE LOADING
# ============================================================

def load_data(company_id: str) -> dict:

    connection = sqlite3.connect(DATABASE_PATH)

    try:

        companies = pd.read_sql_query(
            """
            SELECT
                id,
                company_name,
                website,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            """,
            connection,
        )

        pnl = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                sales,
                expenses,
                operating_profit,
                opm_percentage,
                net_profit,
                eps,
                dividend_payout
            FROM profitandloss
            WHERE company_id = ?
            """,
            connection,
            params=[company_id],
        )

        balance = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                equity_capital,
                reserves,
                borrowings,
                other_liabilities,
                total_liabilities,
                total_assets
            FROM balancesheet
            WHERE company_id = ?
            """,
            connection,
            params=[company_id],
        )

        cashflow = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            WHERE company_id = ?
            """,
            connection,
            params=[company_id],
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                net_profit_margin_pct,
                operating_profit_margin_pct,
                return_on_equity_pct,
                debt_to_equity,
                interest_coverage,
                free_cash_flow_cr,
                earnings_per_share,
                book_value_per_share,
                dividend_payout_ratio_pct,
                total_debt_cr,
                revenue_cagr_5yr,
                pat_cagr_5yr,
                eps_cagr_5yr,
                composite_quality_score,
                return_on_capital_employed_pct,
                return_on_assets_pct
            FROM financial_ratios
            WHERE company_id = ?
            """,
            connection,
            params=[company_id],
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector
            FROM sectors
            WHERE company_id = ?
            """,
            connection,
            params=[company_id],
        )

    finally:

        connection.close()

    company_row = companies[
        companies["id"].astype(str).str.upper()
        == company_id.upper()
    ]

    if company_row.empty:

        raise ValueError(
            f"Company not found in database: {company_id}"
        )

    return {
        "company": company_row.iloc[0].to_dict(),
        "pnl": pnl,
        "balance": balance,
        "cashflow": cashflow,
        "ratios": ratios,
        "sector": (
            sectors.iloc[0].to_dict()
            if not sectors.empty
            else {}
        ),
    }


# ============================================================
# LOAD PROS / CONS
# ============================================================

def load_pros_cons(company_id: str):

    if not PROS_CONS_FILE.exists():

        return [], []

    df = pd.read_csv(
        PROS_CONS_FILE
    )

    if "company_id" not in df.columns:

        return [], []

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    company_df = df[
        df["company_id"] == company_id.upper()
    ].copy()

    pros = company_df[
        company_df["type"]
        .astype(str)
        .str.lower()
        .eq("pro")
    ]

    cons = company_df[
        company_df["type"]
        .astype(str)
        .str.lower()
        .eq("con")
    ]

    pro_texts = (
        pros["text"]
        .dropna()
        .astype(str)
        .tolist()
    )

    con_texts = (
        cons["text"]
        .dropna()
        .astype(str)
        .tolist()
    )

    return pro_texts, con_texts


# ============================================================
# LOAD CAPITAL ALLOCATION
# ============================================================

def load_capital_allocation(company_id: str):

    if not CASHFLOW_INTELLIGENCE_FILE.exists():

        return "Not Available"

    try:

        df = pd.read_excel(
            CASHFLOW_INTELLIGENCE_FILE
        )

    except Exception:

        return "Not Available"

    if "company_id" not in df.columns:

        return "Not Available"

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    row = df[
        df["company_id"] == company_id.upper()
    ]

    if row.empty:

        return "Not Available"

    if "capital_allocation" in row.columns:

        value = row.iloc[0]["capital_allocation"]

    elif "capital_allocation_label" in row.columns:

        value = row.iloc[0]["capital_allocation_label"]

    else:

        return "Not Available"

    if pd.isna(value):

        return "Not Available"

    return str(value)


# ============================================================
# YEAR NORMALIZATION
# ============================================================

def normalize_year(value):

    if pd.isna(value):

        return None

    text = str(value).strip()

    matches = re.findall(
        r"(19\d{2}|20\d{2}|21\d{2})",
        text,
    )

    if matches:

        return int(matches[0])

    return None


def prepare_years(df):

    if df.empty:

        return df.copy()

    result = df.copy()

    result["year_numeric"] = (
        result["year"]
        .map(normalize_year)
    )

    result = result[
        result["year_numeric"].notna()
    ].copy()

    result["year_numeric"] = (
        result["year_numeric"]
        .astype(int)
    )

    return result.sort_values(
        "year_numeric"
    )


# ============================================================
# FORMAT HELPERS
# ============================================================

def safe_number(value):

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

        return float(value)

    except (TypeError, ValueError):

        return None


def format_value(value, suffix=""):

    number = safe_number(value)

    if number is None:

        return "N/A"

    if abs(number) >= 1000:

        return f"{number:,.0f}{suffix}"

    return f"{number:,.2f}{suffix}"


def format_cr(value):

    return format_value(
        value,
        " Cr",
    )


def truncate_text(text, max_length=90):

    text = str(text)

    if len(text) <= max_length:

        return text

    return text[:max_length - 3] + "..."


# ============================================================
# KPI CALCULATION
# ============================================================

def calculate_kpis(data):

    pnl = prepare_years(
        data["pnl"]
    )

    ratios = prepare_years(
        data["ratios"]
    )

    latest_ratio = (
        ratios.iloc[-1]
        if not ratios.empty
        else None
    )

    latest_pnl = (
        pnl.iloc[-1]
        if not pnl.empty
        else None
    )

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    revenue_cagr = None

    if not pnl.empty:

        if len(pnl) >= 6:

            beginning = safe_number(
                pnl.iloc[-6]["sales"]
            )

            ending = safe_number(
                pnl.iloc[-1]["sales"]
            )

            if (
                beginning is not None
                and ending is not None
                and beginning > 0
                and ending > 0
            ):

                revenue_cagr = (
                    (ending / beginning)
                    ** (1 / 5)
                    - 1
                ) * 100

    if revenue_cagr is None and latest_ratio is not None:

        revenue_cagr = safe_number(
            latest_ratio.get(
                "revenue_cagr_5yr"
            )
        )

    # --------------------------------------------------------
    # PAT CAGR
    # --------------------------------------------------------

    pat_cagr = None

    if not pnl.empty and len(pnl) >= 6:

        beginning = safe_number(
            pnl.iloc[-6]["net_profit"]
        )

        ending = safe_number(
            pnl.iloc[-1]["net_profit"]
        )

        if (
            beginning is not None
            and ending is not None
            and beginning > 0
            and ending > 0
        ):

            pat_cagr = (
                (ending / beginning)
                ** (1 / 5)
                - 1
            ) * 100

    if pat_cagr is None and latest_ratio is not None:

        pat_cagr = safe_number(
            latest_ratio.get(
                "pat_cagr_5yr"
            )
        )

    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    roe = None

    if latest_ratio is not None:

        roe = safe_number(
            latest_ratio.get(
                "return_on_equity_pct"
            )
        )

    if roe is None:

        roe = safe_number(
            data["company"].get(
                "roe_percentage"
            )
        )

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    roce = None

    if latest_ratio is not None:

        roce = safe_number(
            latest_ratio.get(
                "return_on_capital_employed_pct"
            )
        )

    if roce is None:

        roce = safe_number(
            data["company"].get(
                "roce_percentage"
            )
        )

    # --------------------------------------------------------
    # Debt / Equity
    # --------------------------------------------------------

    debt_equity = None

    if latest_ratio is not None:

        debt_equity = safe_number(
            latest_ratio.get(
                "debt_to_equity"
            )
        )

    # --------------------------------------------------------
    # Latest EPS
    # --------------------------------------------------------

    eps = None

    if latest_pnl is not None:

        eps = safe_number(
            latest_pnl.get(
                "eps"
            )
        )

    if eps is None and latest_ratio is not None:

        eps = safe_number(
            latest_ratio.get(
                "earnings_per_share"
            )
        )

    # --------------------------------------------------------
    # Quality Score
    # --------------------------------------------------------

    quality = None

    if latest_ratio is not None:

        quality = safe_number(
            latest_ratio.get(
                "composite_quality_score"
            )
        )

    return {
        "revenue_cagr": revenue_cagr,
        "pat_cagr": pat_cagr,
        "roe": roe,
        "roce": roce,
        "debt_equity": debt_equity,
        "eps": eps,
        "quality": quality,
    }


# ============================================================
# PAGE 1 HEADER
# ============================================================

def create_header(
    company_name,
    ticker,
    sector,
):

    title = Paragraph(
        company_name,
        TITLE_STYLE,
    )

    subtitle = Paragraph(
        f"{ticker}  |  {sector}  |  N100 Financial Intelligence",
        SUBTITLE_STYLE,
    )

    table = Table(
        [
            [
                [
                    title,
                    Spacer(1, 2),
                    subtitle,
                ]
            ]
        ],
        colWidths=[CONTENT_WIDTH],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    return table


# ============================================================
# KPI TILES
# ============================================================

def create_kpi_tiles(kpis):

    tiles = [
        (
            "Revenue CAGR",
            format_value(
                kpis["revenue_cagr"],
                "%",
            ),
        ),
        (
            "PAT CAGR",
            format_value(
                kpis["pat_cagr"],
                "%",
            ),
        ),
        (
            "ROE",
            format_value(
                kpis["roe"],
                "%",
            ),
        ),
        (
            "ROCE",
            format_value(
                kpis["roce"],
                "%",
            ),
        ),
        (
            "Debt / Equity",
            format_value(
                kpis["debt_equity"]
            ),
        ),
        (
            "Quality Score",
            format_value(
                kpis["quality"]
            ),
        ),
    ]

    rows = []

    for start in range(
        0,
        len(tiles),
        3,
    ):

        row = []

        for label, value in tiles[start:start + 3]:

            label_para = Paragraph(
                label,
                ParagraphStyle(
                    "KPILabel",
                    parent=SMALL_STYLE,
                    fontName="Helvetica-Bold",
                    textColor=GRAY,
                    alignment=TA_CENTER,
                ),
            )

            value_para = Paragraph(
                value,
                ParagraphStyle(
                    "KPIValue",
                    parent=NORMAL_STYLE,
                    fontName="Helvetica-Bold",
                    fontSize=13,
                    leading=15,
                    textColor=NAVY,
                    alignment=TA_CENTER,
                ),
            )

            tile = Table(
                [
                    [label_para],
                    [value_para],
                ],
                colWidths=[
                    (CONTENT_WIDTH - 8 * mm) / 3
                ],
            )

            tile.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            LIGHT_GRAY,
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            MID_GRAY,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            row.append(tile)

        rows.append(row)

    table = Table(
        rows,
        colWidths=[
            (CONTENT_WIDTH - 8 * mm) / 3
        ] * 3,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    1.3 * mm,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    1.3 * mm,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    1.3 * mm,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    1.3 * mm,
                ),
            ]
        )
    )

    return table


# ============================================================
# CHART HELPERS
# ============================================================

def save_revenue_profit_chart(
    pnl,
    company_id,
):

    pnl = prepare_years(pnl)

    pnl = pnl.tail(10)

    if pnl.empty:

        return None

    path = CHART_DIR / (
        f"{company_id}_revenue_profit.png"
    )

    years = pnl["year_numeric"].astype(str)

    revenue = pd.to_numeric(
        pnl["sales"],
        errors="coerce",
    ).fillna(0)

    profit = pd.to_numeric(
        pnl["net_profit"],
        errors="coerce",
    ).fillna(0)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(8.0, 2.55),
    )

    axes[0].bar(
        years,
        revenue,
    )

    axes[0].set_title(
        "Revenue — 10 Years",
        fontsize=9,
        fontweight="bold",
    )

    axes[0].tick_params(
        axis="x",
        rotation=45,
        labelsize=6,
    )

    axes[0].tick_params(
        axis="y",
        labelsize=6,
    )

    axes[0].grid(
        axis="y",
        alpha=0.2,
    )

    axes[1].bar(
        years,
        profit,
    )

    axes[1].set_title(
        "Net Profit — 10 Years",
        fontsize=9,
        fontweight="bold",
    )

    axes[1].tick_params(
        axis="x",
        rotation=45,
        labelsize=6,
    )

    axes[1].tick_params(
        axis="y",
        labelsize=6,
    )

    axes[1].grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def save_roe_roce_chart(
    ratios,
    company_id,
):

    ratios = prepare_years(ratios)

    ratios = ratios.tail(10)

    if ratios.empty:

        return None

    path = CHART_DIR / (
        f"{company_id}_roe_roce.png"
    )

    years = ratios["year_numeric"]

    roe = pd.to_numeric(
        ratios["return_on_equity_pct"],
        errors="coerce",
    )

    roce = pd.to_numeric(
        ratios["return_on_capital_employed_pct"],
        errors="coerce",
    )

    fig, ax1 = plt.subplots(
        figsize=(8.0, 2.4)
    )

    ax1.plot(
        years,
        roe,
        marker="o",
        linewidth=1.8,
        label="ROE",
    )

    ax1.set_ylabel(
        "ROE (%)",
        fontsize=7,
    )

    ax1.tick_params(
        labelsize=6,
    )

    ax1.grid(
        alpha=0.2,
    )

    ax2 = ax1.twinx()

    ax2.plot(
        years,
        roce,
        marker="s",
        linewidth=1.8,
        linestyle="--",
        label="ROCE",
    )

    ax2.set_ylabel(
        "ROCE (%)",
        fontsize=7,
    )

    ax2.tick_params(
        labelsize=6,
    )

    ax1.set_title(
        "ROE vs ROCE — 10 Years",
        fontsize=9,
        fontweight="bold",
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def save_balance_sheet_chart(
    balance,
    company_id,
):

    balance = prepare_years(balance)

    balance = balance.tail(10)

    if balance.empty:

        return None

    path = CHART_DIR / (
        f"{company_id}_balance_sheet.png"
    )

    years = balance["year_numeric"].astype(str)

    equity = (
        pd.to_numeric(
            balance["equity_capital"],
            errors="coerce",
        ).fillna(0)
        +
        pd.to_numeric(
            balance["reserves"],
            errors="coerce",
        ).fillna(0)
    )

    borrowings = pd.to_numeric(
        balance["borrowings"],
        errors="coerce",
    ).fillna(0)

    other = pd.to_numeric(
        balance["other_liabilities"],
        errors="coerce",
    ).fillna(0)

    fig, ax = plt.subplots(
        figsize=(8.0, 2.45)
    )

    ax.bar(
        years,
        equity,
        label="Equity",
    )

    ax.bar(
        years,
        borrowings,
        bottom=equity,
        label="Borrowings",
    )

    ax.bar(
        years,
        other,
        bottom=equity + borrowings,
        label="Other Liabilities",
    )

    ax.set_title(
        "Balance Sheet Composition",
        fontsize=9,
        fontweight="bold",
    )

    ax.tick_params(
        axis="x",
        rotation=45,
        labelsize=6,
    )

    ax.tick_params(
        axis="y",
        labelsize=6,
    )

    ax.legend(
        fontsize=6,
        loc="upper left",
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


# ============================================================
# CASH FLOW WATERFALL
# ============================================================

def save_cashflow_chart(
    cashflow,
    company_id,
):

    cashflow = prepare_years(cashflow)

    if cashflow.empty:

        return None

    latest = cashflow.iloc[-1]

    values = [
        safe_number(
            latest["operating_activity"]
        ) or 0,
        safe_number(
            latest["investing_activity"]
        ) or 0,
        safe_number(
            latest["financing_activity"]
        ) or 0,
    ]

    labels = [
        "CFO",
        "CFI",
        "CFF",
    ]

    net_cash = (
        safe_number(
            latest["net_cash_flow"]
        )
    )

    if net_cash is None:

        net_cash = sum(values)

    path = CHART_DIR / (
        f"{company_id}_cashflow.png"
    )

    # --------------------------------------------------------
    # Waterfall calculations
    # --------------------------------------------------------

    starts = []
    heights = []

    running = 0

    for value in values:

        if value >= 0:

            starts.append(running)
            heights.append(value)

        else:

            starts.append(running + value)
            heights.append(abs(value))

        running += value

    labels_final = labels + ["Net Cash Flow"]

    bottoms_final = starts + [
        min(0, net_cash)
    ]

    heights_final = heights + [
        abs(net_cash)
    ]

    fig, ax = plt.subplots(
        figsize=(8.0, 2.35)
    )

    x = range(
        len(labels_final)
    )

    ax.bar(
        x,
        heights_final,
        bottom=bottoms_final,
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_xticks(
        list(x)
    )

    ax.set_xticklabels(
        labels_final,
        fontsize=7,
    )

    ax.set_title(
        f"Cash Flow Waterfall — {int(latest['year_numeric'])}",
        fontsize=9,
        fontweight="bold",
    )

    ax.tick_params(
        axis="y",
        labelsize=6,
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


# ============================================================
# WRAPPED PROS / CONS
# ============================================================

def create_bullet_list(
    items,
    style,
    bullet_color,
):

    if not items:

        return Paragraph(
            "No generated items available.",
            style,
        )

    paragraphs = []

    for text in items[:6]:

        safe_text = truncate_text(
            text,
            120,
        )

        paragraphs.append(
            Paragraph(
                f'<font color="{bullet_color}">●</font> '
                f"{safe_text}",
                style,
            )
        )

        paragraphs.append(
            Spacer(1, 2)
        )

    return paragraphs


# ============================================================
# CAPITAL ALLOCATION BADGE
# ============================================================

def create_capital_badge(
    pattern,
):

    badge_text = (
        f"CAPITAL ALLOCATION  |  {pattern}"
    )

    table = Table(
        [
            [
                Paragraph(
                    badge_text,
                    ParagraphStyle(
                        "Badge",
                        parent=NORMAL_STYLE,
                        fontName="Helvetica-Bold",
                        fontSize=9,
                        leading=11,
                        textColor=WHITE,
                        alignment=TA_CENTER,
                    ),
                )
            ]
        ],
        colWidths=[
            CONTENT_WIDTH
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    NAVY,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


# ============================================================
# FOOTER
# ============================================================

def draw_footer(
    canvas,
    doc,
):

    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        6,
    )

    canvas.setFillColor(
        GRAY
    )

    canvas.drawString(
        LEFT_MARGIN,
        7 * mm,
        "N100 Financial Intelligence Platform",
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        7 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# BUILD TEARSHEET
# ============================================================

def build_tearsheet(
    company_id,
    output_path,
):

    print(
        f"\nGenerating tearsheet: {company_id}"
    )

    data = load_data(
        company_id
    )

    company = data["company"]

    company_name = str(
        company.get(
            "company_name",
            company_id,
        )
    ).strip()

    sector = str(
        data["sector"].get(
            "broad_sector",
            "N100",
        )
    ).strip()

    kpis = calculate_kpis(
        data
    )

    pros, cons = load_pros_cons(
        company_id
    )

    capital_allocation = (
        load_capital_allocation(
            company_id
        )
    )

    # --------------------------------------------------------
    # Create chart directory
    # --------------------------------------------------------

    CHART_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Create charts
    # --------------------------------------------------------

    revenue_profit_chart = (
        save_revenue_profit_chart(
            data["pnl"],
            company_id,
        )
    )

    roe_roce_chart = (
        save_roe_roce_chart(
            data["ratios"],
            company_id,
        )
    )

    balance_chart = (
        save_balance_sheet_chart(
            data["balance"],
            company_id,
        )
    )

    cashflow_chart = (
        save_cashflow_chart(
            data["cashflow"],
            company_id,
        )
    )

    # --------------------------------------------------------
    # PDF document
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=f"{company_name} Financial Tearsheet",
        author="N100 Financial Intelligence Platform",
        allowSplitting=1,
    )

    story = []

    # ========================================================
    # PAGE 1
    # ========================================================

    story.append(
        create_header(
            company_name,
            company_id,
            sector,
        )
    )

    story.append(
        Spacer(1, 5)
    )

    story.append(
        create_kpi_tiles(
            kpis
        )
    )

    story.append(
        Spacer(1, 5)
    )

    story.append(
        Paragraph(
            "Financial Performance",
            SECTION_STYLE,
        )
    )

    if revenue_profit_chart:

        story.append(
            Image(
                str(revenue_profit_chart),
                width=CONTENT_WIDTH,
                height=65 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Revenue and Net Profit history unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        Spacer(1, 2)
    )

    if roe_roce_chart:

        story.append(
            Image(
                str(roe_roce_chart),
                width=CONTENT_WIDTH,
                height=53 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "ROE / ROCE history unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        PageBreak()
    )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(
        Paragraph(
            "Balance Sheet & Cash Flow Intelligence",
            SECTION_STYLE,
        )
    )

    if balance_chart:

        story.append(
            Image(
                str(balance_chart),
                width=CONTENT_WIDTH,
                height=57 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Balance Sheet history unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        Spacer(1, 3)
    )

    if cashflow_chart:

        story.append(
            Image(
                str(cashflow_chart),
                width=CONTENT_WIDTH,
                height=52 * mm,
            )
        )

    else:

        story.append(
            Paragraph(
                "Cash Flow history unavailable.",
                SMALL_STYLE,
            )
        )

    story.append(
        Spacer(1, 4)
    )

    # --------------------------------------------------------
    # Pros / Cons
    # --------------------------------------------------------

    pro_flowables = create_bullet_list(
        pros,
        PRO_STYLE,
        "#166534",
    )

    con_flowables = create_bullet_list(
        cons,
        CON_STYLE,
        "#991B1B",
    )

    pro_cell = [
        Paragraph(
            "PROS",
            ParagraphStyle(
                "ProsHeading",
                parent=SECTION_STYLE,
                textColor=GREEN,
                fontSize=9,
            ),
        )
    ]

    if isinstance(
        pro_flowables,
        list,
    ):

        pro_cell.extend(
            pro_flowables
        )

    else:

        pro_cell.append(
            pro_flowables
        )

    con_cell = [
        Paragraph(
            "CONS",
            ParagraphStyle(
                "ConsHeading",
                parent=SECTION_STYLE,
                textColor=RED,
                fontSize=9,
            ),
        )
    ]

    if isinstance(
        con_flowables,
        list,
    ):

        con_cell.extend(
            con_flowables
        )

    else:

        con_cell.append(
            con_flowables
        )

    pros_cons = Table(
        [
            [
                pro_cell,
                con_cell,
            ]
        ],
        colWidths=[
            CONTENT_WIDTH / 2,
            CONTENT_WIDTH / 2,
        ],
    )

    pros_cons.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GREEN,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    LIGHT_RED,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    MID_GRAY,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    MID_GRAY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        pros_cons
    )

    story.append(
        Spacer(1, 4)
    )

    # --------------------------------------------------------
    # Capital allocation
    # --------------------------------------------------------

    story.append(
        create_capital_badge(
            capital_allocation
        )
    )

    # --------------------------------------------------------
    # Build PDF
    # --------------------------------------------------------

    doc.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    print(
        f"[PASS] Created: {output_path}"
    )

    return output_path


# ============================================================
# TEST FIVE COMPANIES
# ============================================================

def run_day33_tests():

    print("=" * 70)
    print("N100 PDF TEARSHEET TEMPLATE")
    print("SPRINT 5 - DAY 33")
    print("=" * 70)

    print(
        f"\nDatabase:"
        f"\n{DATABASE_PATH}"
    )

    print(
        f"\nOutput directory:"
        f"\n{OUTPUT_DIR}"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHART_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    successful = []
    failed = []

    for ticker in TEST_COMPANIES:

        output_path = (
            OUTPUT_DIR
            / f"{ticker}_tearsheet.pdf"
        )

        try:

            build_tearsheet(
                ticker,
                output_path,
            )

            successful.append(
                ticker
            )

        except Exception as exc:

            failed.append(
                (
                    ticker,
                    str(exc),
                )
            )

            print(
                f"[FAIL] {ticker}: {exc}"
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DAY 33 TEST SUMMARY")
    print("=" * 70)

    print(
        f"\nCompanies tested : "
        f"{len(TEST_COMPANIES)}"
    )

    print(
        f"Successful       : "
        f"{len(successful)}"
    )

    print(
        f"Failed           : "
        f"{len(failed)}"
    )

    print(
        "\nSuccessful:"
    )

    for ticker in successful:

        print(
            f"  [PASS] {ticker}"
        )

    if failed:

        print(
            "\nFailures:"
        )

        for ticker, error in failed:

            print(
                f"  [FAIL] {ticker}"
            )

            print(
                f"         {error}"
            )

    print(
        "\nGenerated files:"
    )

    for ticker in successful:

        path = (
            OUTPUT_DIR
            / f"{ticker}_tearsheet.pdf"
        )

        if path.exists():

            size_kb = (
                path.stat().st_size / 1024
            )

            print(
                f"  {path.name:<30} "
                f"{size_kb:.1f} KB"
            )

    if (
        len(successful)
        == len(TEST_COMPANIES)
    ):

        print(
            "\nDAY 33 STATUS: TEMPLATE GENERATED"
        )

        print(
            "Next: visually inspect all 5 PDFs "
            "for overflow, blank pages, and chart rendering."
        )

    else:

        print(
            "\nDAY 33 STATUS: REVIEW REQUIRED"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_day33_tests()