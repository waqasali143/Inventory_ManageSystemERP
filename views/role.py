from tkinter import *
from tkinter import ttk

from services.role_service import (
    load_roles, get_all_sections, get_permissions_for_role_name,
    save_new_role, update_role, delete_role
)
from repositories import role_repository as repo
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.window_helpers import size_and_center
from utils.branding_helpers import add_branding_strip
# ============================================================

def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Role Management")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.55, height_ratio=1, resizable=True)

    apply_app_style()
    win.iconbitmap("assets/ims.ico")

    selected_role_id = StringVar()
    selected_role_name = StringVar()
    new_role_name = StringVar()

    checkbox_vars = {}  # section_key -> BooleanVar

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="ROLE MANAGEMENT",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Roles List ----------------
    list_frame = LabelFrame(
        win, text="Existing Roles (click to edit)", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    list_frame.pack(fill="x", padx=20, pady=15)

    roles_combo = ttk.Combobox(list_frame, state="readonly", width=30)
    roles_combo.pack(side=LEFT, padx=(0, 10))

    role_id_map = {}

    def refresh_roles_list():
        roles = load_roles()
        role_id_map.clear()
        names = []
        for role_id, name in roles:
            role_id_map[name] = role_id
            names.append(name)
        roles_combo["values"] = names

    def on_role_selected(event):
        name = roles_combo.get()
        if not name:
            return

        selected_role_id.set(role_id_map[name])
        selected_role_name.set(name)

        permissions = get_permissions_for_role_name(name)
        for key, var in checkbox_vars.items():
            var.set(key in permissions)

    roles_combo.bind("<<ComboboxSelected>>", on_role_selected)

    Button(list_frame, text="🗑 Delete Selected Role", command=lambda: handle_delete()).pack(side=LEFT)

    # ---------------- New Role Name ----------------
    new_role_frame = LabelFrame(
        win, text="Create New Role", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    new_role_frame.pack(fill="x", padx=20, pady=(0, 15))

    Label(new_role_frame, text="Role Name", bg=BACKGROUND).pack(side=LEFT, padx=(0, 10))
    Entry(new_role_frame, textvariable=new_role_name, width=25).pack(side=LEFT)

    # ---------------- Permissions Checklist ----------------
    perms_frame = LabelFrame(
        win, text="Allowed Sections", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    perms_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    for i, (key, label) in enumerate(get_all_sections()):
        var = BooleanVar(value=False)
        checkbox_vars[key] = var
        Checkbutton(
            perms_frame, text=label, variable=var, bg=BACKGROUND, anchor="w"
        ).grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=5)

    # ---------------- Actions ----------------
    def get_selected_sections():
        return [key for key, var in checkbox_vars.items() if var.get()]

    def handle_create():
        if save_new_role(new_role_name.get(), get_selected_sections()):
            new_role_name.set("")
            for var in checkbox_vars.values():
                var.set(False)
            refresh_roles_list()

    def handle_update():
        if not selected_role_id.get():
            from tkinter import messagebox
            messagebox.showerror("Error", "Select a role from the list first.")
            return
        update_role(int(selected_role_id.get()), selected_role_name.get(), get_selected_sections())

    def handle_delete():
        if not selected_role_id.get():
            from tkinter import messagebox
            messagebox.showerror("Error", "Select a role from the list first.")
            return
        if delete_role(int(selected_role_id.get()), selected_role_name.get()):
            selected_role_id.set("")
            selected_role_name.set("")
            for var in checkbox_vars.values():
                var.set(False)
            refresh_roles_list()

    action_frame = Frame(win, bg=BACKGROUND)
    action_frame.pack(fill="x", padx=20, pady=(0, 20))

    Button(action_frame, text="➕ Create New Role", width=20, command=handle_create).pack(side=LEFT, padx=5)
    Button(action_frame, text="💾 Update Selected Role", width=20, command=handle_update).pack(side=LEFT, padx=5)

    refresh_roles_list()