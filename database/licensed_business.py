# =====================================================================
# Set ONCE per client, before delivering this copy of the app.
# This is the business this specific installation is licensed to.
# It is NOT editable from inside the app - only by editing this file
# directly (developer-only).
# =====================================================================

LOCKED_BUSINESS_NAME = "My Trading Name"   # e.g. "Ahmed Traders" - fill in before delivery

# Path to the client's own logo file (PNG/JPG), used on the branding
# strip of every window and on every printed invoice/receipt/report.
# Place the client's logo file under assets/ before delivery and point
# this at it. Leave as "" if the client has no logo - every place that
# reads this handles a missing/blank logo gracefully (nothing is shown,
# nothing breaks).
LOCKED_BUSINESS_LOGO_PATH = "assets/client_logo.png"   # e.g. "assets/ahmed_traders_logo.png"