
from repositories import settings_repository as repo
from utils import event_bus

# =====================================================================
# Simple in-memory cache so every currency-formatting call across the
# app doesn't hit the database - only refreshed when the setting
# actually changes.
# =====================================================================

_currency_cache = None

def get_currency():
    global _currency_cache

    if _currency_cache is None:
        _currency_cache = repo.fetch_setting("currency", default="Rs")

    return _currency_cache

def set_currency(new_currency):
    global _currency_cache

    repo.save_setting("currency", new_currency)
    _currency_cache = new_currency

    event_bus.publish()  # so any open windows can refresh their labels

def format_currency(amount):
    """
    Central place every screen calls to display a money value.
    Example: format_currency(1500) -> "Rs 1,500.00"
    """
    return f"{get_currency()} {amount:,.2f}"