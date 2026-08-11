from tkinter import *
from tkinter import ttk

from services.user_service import load_users, save_user, set_user_status, get_available_roles
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.tree_helpers import build_treeview, reload_treeview
from utils.ui_helpers import add_buttons, labeled_entry
from utils.window_helpers import size_and_center
from utils.branding_helpers import add_branding_strip


USER_COLUMNS = [
    {"key": "id", "heading": "ID", "width": 60, "anchor": CENTER, "stretch": False},
    {"key": "full_name", "heading": "Full Name", "width": 180, "stretch": True},
    {"key": "username", "heading": "Username", "width": 150, "stretch": False},
    {"key": "role", "heading": "Role", "width": 100, "anchor": CENTER, "stretch": False},
    {"key": "status", "heading": "Status", "width": 100, "anchor": CENTER, "stretch": False},
]


def refresh_users(tree):

    rows = load_users()
    reload_treeview(tree, rows)

    tree.tag_configure("inactive", background="#F3F4F6", foreground="#9CA3AF")

    for row_id in tree.get_children():
        status = tree.item(row_id, "values")[4]
        if status == "Inactive":
            tree.item(row_id, tags=("inactive",))


def get_selected_user(event, tree, selected_id):
    selected = tree.focus()
    values = tree.item(selected, "values")
    if values:
        selected_id.set(values[0])


def handle_save(full_name, username, password, role, tree):
    if save_user(full_name, username, password, role):
        refresh_users(tree)
        full_name.set("")
        username.set("")
        password.set("")


def handle_deactivate(selected_id, tree):
    if set_user_status(selected_id, "Inactive"):
        refresh_users(tree)
        selected_id.set("")


def handle_activate(selected_id, tree):
    if set_user_status(selected_id, "Active"):
        refresh_users(tree)
        selected_id.set("")


def open_window():

    win = Toplevel()
    add_branding_strip(win)
    win.title("User Management")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.6, height_ratio=0.65, resizable=True)

    apply_app_style()

    selected_id = StringVar()
    full_name = StringVar()
    username = StringVar()
    password = StringVar()
    
    available_roles = get_available_roles()
    role = StringVar(value=available_roles[0] if available_roles else "")
    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="USER MANAGEMENT",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Form ----------------
    form_frame = LabelFrame(
        win, text="Add New User", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    form_frame.pack(fill="x", padx=20, pady=15)
    form_frame.columnconfigure((1, 3), weight=1)

    labeled_entry(form_frame, "Full Name", 0, 0, full_name, justify="left")
    labeled_entry(form_frame, "Username", 0, 2, username, justify="left")

    Label(form_frame, text="Password", bg=BACKGROUND).grid(row=1, column=0, padx=10, pady=8, sticky="w")
    Entry(form_frame, textvariable=password, show="•").grid(row=1, column=1, padx=10, pady=8, sticky="ew")

    Label(form_frame, text="Role", bg=BACKGROUND).grid(row=1, column=2, padx=10, pady=8, sticky="w")
    role_combo = ttk.Combobox(form_frame, textvariable=role, values=available_roles, state="readonly")
    role_combo.grid(row=1, column=3, padx=10, pady=8, sticky="ew")

    button_frame = Frame(form_frame, bg=BACKGROUND)
    button_frame.grid(row=2, column=0, columnspan=4, pady=15)
    button_frame.columnconfigure((0, 1, 2), weight=1)

    add_buttons(button_frame, [
        ("💾 Add User", lambda: handle_save(full_name, username, password, role, tree)),
        ("🚫 Deactivate", lambda: handle_deactivate(selected_id, tree)),
        ("✅ Activate", lambda: handle_activate(selected_id, tree)),
    ])

    # ---------------- User Table ----------------
    table_frame = Frame(win, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, USER_COLUMNS)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=tree.yview)
    tree.pack(fill=BOTH, expand=True)

    tree.bind("<Double-1>", lambda event: get_selected_user(event, tree, selected_id))

    refresh_users(tree)