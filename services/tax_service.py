from repositories import settings_repository as repo
from utils import event_bus

# =====================================================================
# Central place for Filer/Non-Filer tax rates. Rates are stored as
# SETTINGS (editable by the owner in Business Settings), never
# hardcoded - when FBR changes rates, the owner updates them here,
# no code change needed anywhere in the app.
# =====================================================================


def get_filer_tax_rate():
    return float(repo.fetch_setting("filer_tax_rate", default="2"))


def get_non_filer_tax_rate():
    return float(repo.fetch_setting("non_filer_tax_rate", default="4"))


def set_tax_rates(filer_rate, non_filer_rate):
    repo.save_setting("filer_tax_rate", str(filer_rate))
    repo.save_setting("non_filer_tax_rate", str(non_filer_rate))
    event_bus.publish()


def get_applicable_tax_rate(is_filer):
    """
    THE single function every module should call.
    is_filer: True/False (or 1/0) - whichever the caller already has.
    Returns the correct tax % to pre-fill in Sales/Purchase forms.
    """
    if is_filer:
        return get_filer_tax_rate()
    return get_non_filer_tax_rate()