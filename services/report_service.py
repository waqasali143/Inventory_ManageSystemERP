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

    product_details = get_product_wise_report(start_date, end_date)

    # Accurate profit: only counts items that were actually SOLD,
    # using each item's real cost at the time it was sold - stock
    # still sitting in inventory never affects this number.
    gross_profit = sum(row[5] for row in product_details)   # row[5] = profit
    total_profit = gross_profit - total_expenses

    # Cost of Goods Sold (COGS) - the actual cost of only the items
    # that were sold in this period, as opposed to total_purchases
    # (everything bought from suppliers, sold or still sitting in
    # stock). Reuses product_details we already fetched above, so
    # no extra query is needed - row[4] is each product's total cost.
    cost_of_sold_items = sum(row[4] for row in product_details)   # row[4] = cost

    sales_tax, purchase_tax = repo.fetch_tax_totals(start_date, end_date)

    best_products = repo.fetch_top_products(start_date, end_date, limit=10, worst=False)
    worst_products = repo.fetch_top_products(start_date, end_date, limit=10, worst=True)

    expense_breakdown = repo.fetch_expense_breakdown(start_date, end_date)

    sales_trend = repo.fetch_daily_sales_trend(start_date, end_date)
    purchase_trend = repo.fetch_daily_purchase_trend(start_date, end_date)

    return {
        "total_sales": total_sales,
        "total_purchases": total_purchases,
        "cost_of_sold_items": cost_of_sold_items,
        "sales_tax": sales_tax,
        "purchase_tax": purchase_tax,
        "total_expenses": total_expenses,
        "gross_profit": gross_profit,
        "total_profit": total_profit,
        "best_products": best_products,
        "worst_products": worst_products,
        "expense_breakdown": expense_breakdown,
        "sales_trend": sales_trend,
        "purchase_trend": purchase_trend,
        "product_details": product_details,
        "unsold_products": get_unsold_products(start_date, end_date),
    }
# =====================================================================
# PRODUCT-WISE DETAILED BREAKDOWN
# For each product: total qty sold, revenue, its proportional share
# of each invoice's discount, its cost (at time of sale), and profit.
# =====================================================================
def get_product_wise_report(start_date, end_date):

    raw_rows = repo.fetch_product_wise_raw(start_date, end_date)

    products = {}

    for name, qty, sale_price, cost_price, subtotal, sale_gross, sale_discount, sale_net, sale_amount_paid in raw_rows:

        # This item's proportional share of its invoice's discount:
        # (this item's subtotal / invoice's gross total) * invoice discount
        if sale_gross > 0:
            allocated_discount = (subtotal / sale_gross) * sale_discount
        else:
            allocated_discount = 0.0

        # Same proportional-allocation approach for how much of this
        # item's share is still unpaid. balance_due is 0 for fully
        # paid sales, so this naturally comes out to 0 for them.
        sale_balance_due = sale_net - sale_amount_paid
        if sale_gross > 0:
            allocated_credit = (subtotal / sale_gross) * sale_balance_due
        else:
            allocated_credit = 0.0

        cost = cost_price * qty
        profit = subtotal - allocated_discount - cost

        if name not in products:
            products[name] = {
                "qty": 0,
                "revenue": 0.0,
                "discount": 0.0,
                "cost": 0.0,
                "profit": 0.0,
                "credit": 0.0,
            }

        products[name]["qty"] += qty
        products[name]["revenue"] += subtotal
        products[name]["discount"] += allocated_discount
        products[name]["cost"] += cost
        products[name]["profit"] += profit
        products[name]["credit"] += allocated_credit

    # Convert to a sorted list (highest profit first)
    
    stock_map = repo.fetch_current_stock_map()

    result = [
        (
            name,
            data["qty"],
            data["revenue"],
            data["discount"],
            data["cost"],
            data["profit"],
            stock_map.get(name, 0),
            data["credit"],
        )
        for name, data in products.items()
    ]

    result.sort(key=lambda row: row[5], reverse=True)

    return result
# ================================================================
# ==== Unsolved Products Wraper =============
def get_unsold_products(start_date, end_date):
    return repo.fetch_unsold_products(start_date, end_date)