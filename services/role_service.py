from tkinter import messagebox
from repositories import role_repository as repo
from utils import event_bus
# ==================================================================
PROTECTED_ROLE = "Admin"

def load_roles():
    return repo.fetch_roles()

def get_all_sections():
    return repo.ALL_SECTIONS

def get_permissions_for_role_name(role_name):
    """Admin always has every permission - even if someone edits the
    Admin role's checkboxes, this keeps the app from ever locking
    everyone out by accident."""

    if role_name == PROTECTED_ROLE:
        return {key for key, _label in repo.ALL_SECTIONS}

    return repo.fetch_permissions_for_role_name(role_name)

def save_new_role(role_name, selected_sections):

    role_name = role_name.strip()

    if role_name == "":
        messagebox.showerror("Validation Error", "Role name is required.")
        return False

    if repo.fetch_role_by_name(role_name):
        messagebox.showerror("Error", "A role with this name already exists.")
        return False

    if not selected_sections:
        messagebox.showerror("Validation Error", "Select at least one section for this role.")
        return False

    repo.insert_role(role_name, selected_sections)

    event_bus.publish()

    messagebox.showinfo("Success", "Role created successfully.")
    return True

def update_role(role_id, role_name, selected_sections):

    if role_name == PROTECTED_ROLE:
        messagebox.showerror("Error", "The Admin role cannot be edited - it always has full access.")
        return False

    if not selected_sections:
        messagebox.showerror("Validation Error", "Select at least one section for this role.")
        return False

    repo.update_role_permissions(role_id, selected_sections)

    event_bus.publish()

    messagebox.showinfo("Success", "Role updated successfully.")
    return True

def delete_role(role_id, role_name):

    if role_name == PROTECTED_ROLE:
        messagebox.showerror("Error", "The Admin role cannot be deleted.")
        return False

    confirm = messagebox.askyesno("Confirm Delete", f"Delete role '{role_name}'? Users with this role will need a new role assigned.")
    if not confirm:
        return False

    repo.delete_role(role_id)

    event_bus.publish()

    messagebox.showinfo("Success", "Role deleted.")
    return True