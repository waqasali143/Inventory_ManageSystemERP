from datetime import date, timedelta
from repositories import report_repository as repo


# =====================================================================
# DATE RANGE HELPERS
# =====================================================================
def get_weekly_range():
    end = date.today()
    start = end - timedelta(days=6)
    return start.isoformat(), end.isoformat()
# =========================================================
def get_monthly_range():
    end = date.today()
    start = end - timedelta(days=29)
    return start.isoformat(), end.isoformat()
# =======================================================
def get_custom_range(start_str, end_str):
    """
    Returns (start, end, error). error is None if valid.
    """
    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except ValueError:
        return None, None, "Dates must be in YYYY-MM-DD format."

    if start > end:
        return None, None, "Start date cannot be after End date."

    return start.isoformat(), end.isoformat(), None

# =====================================================================
# MAIN REPORT DATA
# (one function that gathers everything the Reports window needs,
#  so the view only has to make a single call)
# =====================================================================
def get_report_data(start_date, end_date):

    total_sales, total_purchases, total_expenses = repo.fetch_totals(start_date, end_date)

    gross_profit = repo.fetch_gross_profit(start_date, end_date)
    net_profit = gross_profit - total_expenses

    best_products = repo.fetch_top_products(start_date, end_date, limit=10, worst=False)
    worst_products = repo.fetch_top_products(start_date, end_date, limit=10, worst=True)

    expense_breakdown = repo.fetch_expense_breakdown(start_date, end_date)

    sales_trend = repo.fetch_daily_sales_trend(start_date, end_date)
    purchase_trend = repo.fetch_daily_purchase_trend(start_date, end_date)

    return {
        "total_sales": total_sales,
        "total_purchases": total_purchases,
        "total_expenses": total_expenses,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "best_products": best_products,
        "worst_products": worst_products,
        "expense_breakdown": expense_breakdown,
        "sales_trend": sales_trend,
        "purchase_trend": purchase_trend,
    }