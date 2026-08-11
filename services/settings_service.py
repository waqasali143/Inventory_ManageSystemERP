
from repositories import settings_repository as repo
from utils import event_bus
from database.licensed_business import LOCKED_BUSINESS_NAME

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

# =====================================================================
# Business Info (for invoice letterhead)
# =====================================================================

def get_business_info():
    return {
        "name": LOCKED_BUSINESS_NAME,
        "address": repo.fetch_setting("business_address", default=""),
        "phone": repo.fetch_setting("business_phone", default=""),
        "ntn": repo.fetch_setting("business_ntn", default=""),
    }


def save_business_info(address, phone, ntn):
    repo.save_setting("business_address", address)
    repo.save_setting("business_phone", phone)
    repo.save_setting("business_ntn", ntn)
    event_bus.publish()
# ==============================================================================

def get_app_title():
    business_name = get_business_info()["name"]
    if business_name:
        return f"Inventra ERP — {business_name}"
    return "Inventra ERP"