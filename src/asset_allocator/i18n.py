"""Lightweight UI localization for the dashboard (English + Vietnamese).

These are display strings only — no personal data, no secrets. NOT FINANCIAL ADVICE
applies in every language. Add a language by extending _UI and _BUCKETS with the same keys.
"""

from __future__ import annotations

LANGUAGES = ("en", "vi")

_UI: dict[str, dict[str, str]] = {
    "en": {
        "title": "Asset Allocator Dashboard",
        "subtitle": "Net-worth and allocation overview",
        "net_worth": "Net worth",
        "total_pnl": "Total P&L",
        "invested": "Total cost",
        "largest_bucket": "Largest bucket",
        "as_of": "As of",
        "currency": "Currency",
        "allocation": "Allocation by bucket",
        "value_history": "Value history",
        "cashflow": "Cash flow",
        "income_mo": "Income / mo",
        "expense_mo": "Expense / mo",
        "surplus_mo": "Surplus / mo",
        "savings_rate": "Savings rate",
        "runway": "Liquid runway",
        "months": "months",
        "per_year": "/ yr",
        "stale_prices": "Stale prices",
        "none": "None",
        "snapshots": "snapshots",
        "col_bucket": "Bucket",
        "col_value": "Value",
        "col_cost": "Cost",
        "col_pnl": "P&L",
        "col_pnl_pct": "P&L %",
        "col_current": "Current",
        "col_target": "Target",
        "col_drift": "Drift",
        "disclaimer": (
            "NOT FINANCIAL ADVICE. This dashboard shows arithmetic from your inputs and "
            "illustrative, user-tunable defaults."
        ),
    },
    "vi": {
        "title": "Bảng phân bổ tài sản",
        "subtitle": "Tổng quan giá trị ròng và phân bổ",
        "net_worth": "Giá trị ròng",
        "total_pnl": "Tổng lãi/lỗ",
        "invested": "Tổng giá vốn",
        "largest_bucket": "Nhóm lớn nhất",
        "as_of": "Cập nhật",
        "currency": "Tiền tệ",
        "allocation": "Phân bổ theo nhóm",
        "value_history": "Lịch sử giá trị",
        "cashflow": "Dòng tiền",
        "income_mo": "Thu nhập / tháng",
        "expense_mo": "Chi phí / tháng",
        "surplus_mo": "Thặng dư / tháng",
        "savings_rate": "Tỷ lệ tiết kiệm",
        "runway": "Quỹ lỏng (số tháng)",
        "months": "tháng",
        "per_year": "/ năm",
        "stale_prices": "Giá cũ",
        "none": "Không",
        "snapshots": "mốc",
        "col_bucket": "Nhóm tài sản",
        "col_value": "Giá trị",
        "col_cost": "Giá vốn",
        "col_pnl": "Lãi/lỗ",
        "col_pnl_pct": "Lãi/lỗ %",
        "col_current": "Hiện tại",
        "col_target": "Mục tiêu",
        "col_drift": "Lệch",
        "disclaimer": (
            "KHÔNG PHẢI LỜI KHUYÊN TÀI CHÍNH. Bảng này chỉ tính toán số học từ dữ liệu bạn "
            "nhập và các giá trị minh hoạ có thể tự điều chỉnh."
        ),
    },
}

_BUCKETS: dict[str, dict[str, str]] = {
    "en": {
        "equity": "Equity",
        "bonds": "Bonds",
        "gold": "Gold",
        "real_estate": "Real estate",
        "savings": "Savings",
        "cash": "Cash",
        "emergency": "Emergency",
    },
    "vi": {
        "equity": "Cổ phiếu",
        "bonds": "Trái phiếu",
        "gold": "Vàng",
        "real_estate": "Bất động sản",
        "savings": "Tiết kiệm",
        "cash": "Tiền mặt",
        "emergency": "Quỹ khẩn cấp",
    },
}


def normalize_lang(lang: str) -> str:
    return lang if lang in LANGUAGES else "en"


def t(lang: str, key: str) -> str:
    """Translate a UI key, falling back to English then the raw key."""
    lang = normalize_lang(lang)
    return _UI[lang].get(key) or _UI["en"].get(key, key)


def bucket_label(lang: str, bucket: str) -> str:
    """Localized display name for a bucket, falling back to the raw bucket id."""
    lang = normalize_lang(lang)
    return _BUCKETS[lang].get(bucket, bucket)
