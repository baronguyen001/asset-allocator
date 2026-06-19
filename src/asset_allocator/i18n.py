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
        "edit": "Edit",
        "save": "Save changes",
        "saved": "Saved",
        "save_failed": "Save failed",
        "add": "Add",
        "delete": "Delete",
        "detail_income": "Income detail",
        "detail_expense": "Expense detail",
        "detail_holdings": "Holdings detail",
        "goals": "Goals",
        "goal_progress": "Goal progress",
        "target_nw": "Target net worth",
        "gap": "Gap",
        "years_left": "Years left",
        "required_return": "Required return / yr",
        "chart_expense_cat": "Expense by category",
        "chart_income_expense": "Income vs expense",
        "chart_savings": "Savings rate",
        "chart_history": "Net-worth history",
        "chart_goals": "Net worth vs goals",
        "projected": "Projected",
        "unit_note": "Unit",
        "category": "Category",
        "amount": "Amount",
        "freq": "Frequency",
        "year": "Year",
        "kind": "Type",
        "label": "Label",
        "income": "Income",
        "expense": "Expense",
        "monthly": "monthly",
        "yearly": "yearly",
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
        "edit": "Sửa",
        "save": "Lưu thay đổi",
        "saved": "Đã lưu",
        "save_failed": "Lưu thất bại",
        "add": "Thêm",
        "delete": "Xoá",
        "detail_income": "Chi tiết thu nhập",
        "detail_expense": "Chi tiết chi phí",
        "detail_holdings": "Chi tiết tài sản",
        "goals": "Mục tiêu",
        "goal_progress": "Tiến độ mục tiêu",
        "target_nw": "Giá trị ròng mục tiêu",
        "gap": "Còn thiếu",
        "years_left": "Số năm còn lại",
        "required_return": "Lợi suất cần / năm",
        "chart_expense_cat": "Chi phí theo nhóm",
        "chart_income_expense": "Thu vs Chi",
        "chart_savings": "Tỷ lệ tiết kiệm",
        "chart_history": "Lịch sử giá trị ròng",
        "chart_goals": "Giá trị ròng vs mục tiêu",
        "projected": "Dự phóng",
        "unit_note": "Đơn vị",
        "category": "Nhóm",
        "amount": "Số tiền",
        "freq": "Tần suất",
        "year": "Năm",
        "kind": "Loại",
        "label": "Tên",
        "income": "Thu nhập",
        "expense": "Chi phí",
        "monthly": "hàng tháng",
        "yearly": "hàng năm",
        "disclaimer": (
            "KHÔNG PHẢI LỜI KHUYÊN TÀI CHÍNH. Bảng này chỉ tính toán số học từ dữ liệu bạn "
            "nhập và các giá trị minh hoạ có thể tự điều chỉnh."
        ),
    },
}

# Emoji icons by free-text category keyword (lowercased substring match) and by bucket.
_CATEGORY_EMOJI: list[tuple[tuple[str, ...], str]] = [
    (("lương", "luong", "salary", "work", "wage"), "💰"),
    (("thuê", "thue", "rent", "rental"), "🏠"),
    (("giáo", "giao", "học", "hoc", "edu", "school", "kid"), "🎓"),
    (("y tế", "y te", "health", "medic", "khám", "kham", "thuốc", "thuoc"), "🏥"),
    (("con", "child", "đồ chơi", "do choi", "toy"), "🧸"),
    (("đi lại", "di lai", "xăng", "xang", "transport", "fuel", "car"), "🚗"),
    (("cá nhân", "ca nhan", "personal", "tóc", "toc"), "✂️"),
    (("xã hội", "xa hoi", "social", "hiếu", "hieu", "cưới", "cuoi", "gift"), "🎁"),
    (("tết", "tet", "lễ", "le", "season", "holiday"), "🧧"),
    (("du lịch", "du lich", "travel", "leisure", "giải trí", "giai tri"), "✈️"),
    (("bảo", "bao", "insur", "protect"), "🛡️"),
    (("sinh hoạt", "sinh hoat", "living", "điện", "dien", "nước", "nuoc", "ăn", "food"), "🧺"),
]

_BUCKET_EMOJI: dict[str, str] = {
    "equity": "📈",
    "bonds": "📜",
    "gold": "🥇",
    "real_estate": "🏢",
    "savings": "🏦",
    "cash": "💵",
    "emergency": "🆘",
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


def category_emoji(category: str) -> str:
    """Pick an emoji for a free-text cash-flow category (keyword match), else a default."""
    text = (category or "").lower()
    for keywords, emoji in _CATEGORY_EMOJI:
        if any(keyword in text for keyword in keywords):
            return emoji
    return "📦"


def bucket_emoji(bucket: str) -> str:
    """Emoji for an asset bucket id."""
    return _BUCKET_EMOJI.get(bucket, "📦")
