"""
Financial Glossary API for FinRAG.

Provides a curated dictionary of essential financial terms
for retail investors. No LLM calls — instant responses.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Glossary"])


# ── Models ────────────────────────────────────────────

class GlossaryTerm(BaseModel):
    term: str
    category: str
    definition: str
    formula: Optional[str] = None
    example: Optional[str] = None
    why_it_matters: str


# ── Financial Terms Dictionary ────────────────────────

FINANCIAL_GLOSSARY: List[dict] = [
    # ── Profitability Ratios ──
    {
        "term": "Return on Equity (ROE)",
        "category": "Profitability",
        "definition": "Measures how effectively a company uses shareholders' equity to generate profits.",
        "formula": "Net Income / Shareholders' Equity × 100",
        "example": "If net income is $10M and equity is $50M, ROE = 20%",
        "why_it_matters": "Higher ROE indicates efficient use of investor capital. Compare within industry — above 15% is generally strong."
    },
    {
        "term": "Earnings Per Share (EPS)",
        "category": "Profitability",
        "definition": "The portion of a company's profit allocated to each outstanding share of common stock.",
        "formula": "(Net Income - Preferred Dividends) / Weighted Average Shares Outstanding",
        "example": "If net income is $100M with 50M shares, EPS = $2.00",
        "why_it_matters": "EPS growth over time signals increasing profitability. Used as base for P/E ratio calculation."
    },
    {
        "term": "Net Profit Margin",
        "category": "Profitability",
        "definition": "The percentage of revenue remaining as profit after all expenses, taxes, and costs.",
        "formula": "Net Income / Revenue × 100",
        "example": "Revenue of $1B with net income of $100M = 10% margin",
        "why_it_matters": "Shows how much of each dollar earned translates to profit. Higher margins suggest pricing power and cost efficiency."
    },
    {
        "term": "EBITDA",
        "category": "Profitability",
        "definition": "Earnings Before Interest, Taxes, Depreciation, and Amortization — a measure of operating performance.",
        "formula": "Operating Income + Depreciation + Amortization",
        "example": "Operating income $50M + D&A $10M = EBITDA $60M",
        "why_it_matters": "Strips out non-operating effects to compare core business profitability across companies."
    },
    {
        "term": "Gross Margin",
        "category": "Profitability",
        "definition": "The percentage of revenue remaining after subtracting the cost of goods sold (COGS).",
        "formula": "(Revenue - COGS) / Revenue × 100",
        "example": "Revenue $500M - COGS $300M = 40% gross margin",
        "why_it_matters": "Indicates pricing power and production efficiency. Tech companies often have 60%+ margins, retail 20-30%."
    },

    # ── Valuation Ratios ──
    {
        "term": "Price-to-Earnings Ratio (P/E)",
        "category": "Valuation",
        "definition": "The ratio of a company's share price to its earnings per share.",
        "formula": "Share Price / EPS",
        "example": "Stock at $100 with EPS of $5 has a P/E of 20x",
        "why_it_matters": "Indicates how much investors are willing to pay per dollar of earnings. High P/E can mean growth expectations or overvaluation."
    },
    {
        "term": "Price-to-Book Ratio (P/B)",
        "category": "Valuation",
        "definition": "Compares a company's market value to its book value (net assets).",
        "formula": "Market Price per Share / Book Value per Share",
        "example": "Stock at $50 with book value $25 = P/B of 2.0x",
        "why_it_matters": "P/B below 1.0 may indicate undervaluation (or fundamental issues). Useful for banks and asset-heavy companies."
    },
    {
        "term": "Enterprise Value (EV)",
        "category": "Valuation",
        "definition": "The total value of a company including market cap, debt, and cash — represents the acquisition price.",
        "formula": "Market Cap + Total Debt - Cash & Equivalents",
        "example": "Market cap $1B + debt $200M - cash $100M = EV $1.1B",
        "why_it_matters": "More complete than market cap alone. Used in EV/EBITDA ratio for comparing companies with different capital structures."
    },
    {
        "term": "Dividend Yield",
        "category": "Valuation",
        "definition": "Annual dividends per share expressed as a percentage of the share price.",
        "formula": "Annual Dividends per Share / Price per Share × 100",
        "example": "$3 annual dividend on $60 stock = 5% yield",
        "why_it_matters": "Represents cash return on investment. High yields attract income investors but may signal limited growth."
    },
    {
        "term": "PEG Ratio",
        "category": "Valuation",
        "definition": "Price/Earnings ratio adjusted for the company's earnings growth rate.",
        "formula": "P/E Ratio / Annual EPS Growth Rate",
        "example": "P/E of 30 with 15% growth = PEG of 2.0",
        "why_it_matters": "A PEG of 1.0 suggests fair value. Below 1.0 may indicate undervaluation relative to growth."
    },

    # ── Leverage Ratios ──
    {
        "term": "Debt-to-Equity Ratio (D/E)",
        "category": "Leverage",
        "definition": "Measures the proportion of debt financing relative to equity financing.",
        "formula": "Total Liabilities / Shareholders' Equity",
        "example": "Total debt $400M / equity $800M = D/E of 0.5",
        "why_it_matters": "Higher ratios mean more financial risk. A D/E above 2.0 is usually concerning, but norms vary by industry."
    },
    {
        "term": "Interest Coverage Ratio",
        "category": "Leverage",
        "definition": "How easily a company can pay interest on its outstanding debt from operating earnings.",
        "formula": "EBIT / Interest Expense",
        "example": "EBIT $50M / interest $10M = 5x coverage",
        "why_it_matters": "Below 1.5x is a warning sign. The company may struggle to meet debt obligations."
    },
    {
        "term": "Current Ratio",
        "category": "Leverage",
        "definition": "Measures a company's ability to pay short-term obligations with current assets.",
        "formula": "Current Assets / Current Liabilities",
        "example": "Current assets $200M / current liabilities $100M = 2.0x",
        "why_it_matters": "Below 1.0 signals potential liquidity problems. Between 1.5-3.0 is generally healthy."
    },

    # ── Growth Metrics ──
    {
        "term": "Revenue Growth Rate",
        "category": "Growth",
        "definition": "The year-over-year percentage increase in a company's total revenue.",
        "formula": "(Current Year Revenue - Previous Year Revenue) / Previous Year Revenue × 100",
        "example": "Revenue grew from $800M to $1B = 25% growth",
        "why_it_matters": "Consistent revenue growth indicates market demand and competitive strength."
    },
    {
        "term": "Free Cash Flow (FCF)",
        "category": "Growth",
        "definition": "Cash generated by operations minus capital expenditures — represents cash available for shareholders.",
        "formula": "Operating Cash Flow - Capital Expenditures",
        "example": "Operating cash flow $150M - CapEx $50M = FCF $100M",
        "why_it_matters": "FCF funds dividends, buybacks, and debt reduction. Positive FCF growth indicates financial health."
    },
    {
        "term": "CAGR",
        "category": "Growth",
        "definition": "Compound Annual Growth Rate — the mean annual growth rate over a specified period.",
        "formula": "(End Value / Start Value)^(1/n) - 1",
        "example": "Revenue grew from $100M to $200M in 5 years = ~14.9% CAGR",
        "why_it_matters": "Smooths out volatility to show true growth trend. Used to compare investments over different time periods."
    },

    # ── Financial Statements ──
    {
        "term": "Balance Sheet",
        "category": "Financial Statements",
        "definition": "A snapshot of a company's assets, liabilities, and shareholders' equity at a specific point in time.",
        "formula": "Assets = Liabilities + Shareholders' Equity",
        "example": "Assets $1B = Liabilities $400M + Equity $600M",
        "why_it_matters": "Shows what a company owns vs. what it owes. The fundamental accounting equation must always balance."
    },
    {
        "term": "Income Statement (P&L)",
        "category": "Financial Statements",
        "definition": "Reports a company's revenue, expenses, and profit over a specific period (quarter or year).",
        "formula": "Revenue - Expenses = Net Income",
        "example": "Revenue $1B - Total expenses $900M = Net income $100M",
        "why_it_matters": "Shows profitability trends. Look at revenue growth, margin expansion, and bottom-line profit."
    },
    {
        "term": "Cash Flow Statement",
        "category": "Financial Statements",
        "definition": "Shows how cash moves through a company via operations, investing, and financing activities.",
        "formula": None,
        "example": "Operating CF $150M + Investing CF -$50M + Financing CF -$30M = Net change $70M",
        "why_it_matters": "Cash flow is harder to manipulate than earnings. Positive operating cash flow is essential for sustainability."
    },

    # ── Regulatory & Filing ──
    {
        "term": "10-K Filing",
        "category": "Regulatory",
        "definition": "Annual report filed with the SEC containing comprehensive summary of a company's financial performance.",
        "formula": None,
        "example": "Apple's 10-K includes financial statements, risk factors, management discussion, and business overview.",
        "why_it_matters": "The most comprehensive public document about a company. Required reading for serious fundamental analysis."
    },
    {
        "term": "10-Q Filing",
        "category": "Regulatory",
        "definition": "Quarterly report filed with the SEC — less detailed than the 10-K but provides interim updates.",
        "formula": None,
        "example": "Filed three times per year (Q1, Q2, Q3). Q4 is covered by the annual 10-K.",
        "why_it_matters": "Tracks quarterly trends and provides early signals of changing business dynamics."
    },
    {
        "term": "MD&A",
        "category": "Regulatory",
        "definition": "Management's Discussion and Analysis — a section where leadership explains financial results and outlook.",
        "formula": None,
        "example": "The MD&A section explains why revenue declined and what management plans to do about it.",
        "why_it_matters": "Provides qualitative context that numbers alone cannot. Look for management's tone and forward guidance."
    },

    # ── Market Metrics ──
    {
        "term": "Market Capitalization",
        "category": "Market",
        "definition": "The total market value of a company's outstanding shares of stock.",
        "formula": "Share Price × Total Shares Outstanding",
        "example": "Stock at $150 × 1B shares = $150B market cap",
        "why_it_matters": "Classifies companies as large-cap (>$10B), mid-cap ($2-10B), or small-cap (<$2B). Affects risk profile."
    },
    {
        "term": "Beta",
        "category": "Market",
        "definition": "Measures a stock's volatility relative to the overall market.",
        "formula": "Covariance(Stock, Market) / Variance(Market)",
        "example": "Beta of 1.5 means the stock moves 50% more than the market on average",
        "why_it_matters": "Beta > 1 means higher volatility (more risk/reward). Beta < 1 means lower volatility (defensive)."
    },
    {
        "term": "52-Week High/Low",
        "category": "Market",
        "definition": "The highest and lowest price at which a stock has traded during the past 52 weeks.",
        "formula": None,
        "example": "52-week range: $85 - $145. Current price $120 is near the middle of the range.",
        "why_it_matters": "Provides context for current price. Trading near 52-week high may indicate momentum; near low may signal opportunity or risk."
    },

    # ── Risk Metrics ──
    {
        "term": "Sharpe Ratio",
        "category": "Risk",
        "definition": "Measures risk-adjusted return — how much excess return per unit of risk.",
        "formula": "(Portfolio Return - Risk-Free Rate) / Standard Deviation of Portfolio",
        "example": "Return 12%, risk-free rate 3%, std dev 10% = Sharpe of 0.9",
        "why_it_matters": "Higher is better. Above 1.0 is good, above 2.0 is very good. Helps compare investments with different risk levels."
    },
    {
        "term": "Working Capital",
        "category": "Risk",
        "definition": "The difference between current assets and current liabilities — measures short-term financial health.",
        "formula": "Current Assets - Current Liabilities",
        "example": "Current assets $500M - current liabilities $300M = working capital $200M",
        "why_it_matters": "Negative working capital can signal cash flow problems. Positive and growing working capital indicates stability."
    },
]


# ── Endpoints ─────────────────────────────────────────

@router.get(
    "/glossary",
    response_model=List[GlossaryTerm],
    summary="Financial Glossary",
    description="Get a curated list of essential financial terms with definitions and formulas."
)
async def get_glossary(
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """Get financial glossary terms."""
    terms = FINANCIAL_GLOSSARY
    
    if category:
        terms = [t for t in terms if t["category"].lower() == category.lower()]
    
    return [GlossaryTerm(**t) for t in terms]


@router.get(
    "/glossary/search",
    response_model=List[GlossaryTerm],
    summary="Search Glossary",
    description="Search financial terms by keyword."
)
async def search_glossary(
    q: str = Query(..., min_length=1, description="Search query"),
):
    """Search glossary terms."""
    query = q.lower()
    results = [
        GlossaryTerm(**t) for t in FINANCIAL_GLOSSARY
        if query in t["term"].lower() 
        or query in t["definition"].lower()
        or query in t["category"].lower()
    ]
    return results


@router.get(
    "/glossary/categories",
    summary="Glossary Categories",
    description="Get list of available glossary categories."
)
async def get_categories():
    """Get distinct glossary categories."""
    categories = sorted(set(t["category"] for t in FINANCIAL_GLOSSARY))
    return {
        "categories": categories,
        "total_terms": len(FINANCIAL_GLOSSARY)
    }
