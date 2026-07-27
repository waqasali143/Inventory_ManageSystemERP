# =====================================================================
# Lightweight Event Bus (Observer Pattern)
#
# Purpose: when data changes anywhere (a purchase saved, a product
# added...), interested screens (like the Dashboard) should update
# automatically - without polling the database every few seconds
# and without the service layer needing to know Dashboard exists.
#
# How it works:
#   1. A screen "subscribes" a function it wants called on any change.
#   2. A service "publishes" after a successful commit.
#   3. Every subscribed function runs immediately.
#
# This keeps services and views decoupled - purchase_service.py
# never imports dashboard.py, it just shouts "data changed!" and
# whoever is listening reacts.
# =====================================================================

_subscribers = []


def subscribe(callback):
    """Register a function to be called whenever data changes."""
    if callback not in _subscribers:
        _subscribers.append(callback)


def unsubscribe(callback):
    """Stop calling this function (call when a window is closed)."""
    if callback in _subscribers:
        _subscribers.remove(callback)


def publish():
    """Notify all subscribers that data has changed."""
    for callback in list(_subscribers):
        try:
            callback()
        except Exception as e:
            print("Event bus subscriber error:", e)
