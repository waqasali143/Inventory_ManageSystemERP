from repositories import user_repository as repo
from services.role_service import get_permissions_for_role_name

# =====================================================================
# Tracks the currently logged-in user for the whole app session.
# =====================================================================

_current_user = {"id": None, "full_name": None, "role": None}
_current_permissions = set()


def login(username, password):

    row = repo.verify_login(username, password)

    if row is None:
        return False

    user_id, full_name, role = row

    _current_user["id"] = user_id
    _current_user["full_name"] = full_name
    _current_user["role"] = role

    global _current_permissions
    _current_permissions = get_permissions_for_role_name(role)

    repo.update_last_login(user_id)

    return True


def logout():
    global _current_permissions
    _current_user["id"] = None
    _current_user["full_name"] = None
    _current_user["role"] = None
    _current_permissions = set()


def get_current_user():
    return dict(_current_user)


def is_admin():
    return _current_user["role"] == "Admin"


def has_permission(section):
    """Use this everywhere instead of is_admin() to check if the
    current user's role can access a given section (e.g. 'products',
    'reports', 'users')."""
    return section in _current_permissions


def is_logged_in():
    return _current_user["id"] is not None