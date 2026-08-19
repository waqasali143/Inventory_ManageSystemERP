import os
import subprocess
import sys
from tkinter import *
from tkinter import ttk, messagebox

from services.backup_service import (
    create_backup, list_backups, restore_backup, format_size, BACKUP_FOLDER
)
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
    apply_app_style
)
from utils.branding_helpers import add_branding_strip
from utils.tree_helpers import build_treeview
from utils.window_helpers import size_and_center

BACKUP_COLUMNS = [
    {"key": "filename", "heading": "Backup File", "width": 260, "stretch": True},
    {"key": "modified", "heading": "Created", "width": 170, "anchor": CENTER, "stretch": False},
    {"key": "size", "heading": "Size", "width": 100, "anchor": E, "stretch": False},
]


def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Backup & Restore")
    size_and_center(win, width_ratio=0.55, height_ratio=1, resizable=True)

    win.configure(bg=BACKGROUND)

    apply_app_style()
    win.iconbitmap("assets/ims.ico")

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="BACKUP & RESTORE",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    Label(
        header_frame, text="A backup is also taken automatically every time the app closes",
        bg=PRIMARY, fg=WHITE, font=FONT_BODY
    ).pack(side=RIGHT, padx=20)

    # ---------------- Info note ----------------
    Label(
        win,
        text="Keeping backups only on this computer is risky - if the disk fails or the "
             "laptop is lost, these are lost too. Periodically copy the \"backups\" folder "
             "to a USB drive or a cloud folder (Google Drive / OneDrive) as well.",
        bg=BACKGROUND, fg="gray30", font=("Segoe UI", 8), wraplength=650, justify=LEFT
    ).pack(anchor="w", padx=20, pady=(12, 0))

    # ---------------- Table ----------------
    table_frame = Frame(win, bg=BACKGROUND)
    table_frame.pack(fill=BOTH, expand=True, padx=20, pady=15)

    scrollbar_y = Scrollbar(table_frame)
    scrollbar_y.pack(side=RIGHT, fill=Y)

    tree = build_treeview(table_frame, BACKUP_COLUMNS, height=12)
    tree.configure(yscrollcommand=scrollbar_y.set)
    scrollbar_y.config(command=tree.yview)
    tree.pack(fill=BOTH, expand=True)

    def refresh():
        for row in tree.get_children():
            tree.delete(row)

        for backup in list_backups():
            tree.insert("", END, values=(
                backup["filename"],
                backup["modified"].strftime("%Y-%m-%d %H:%M:%S"),
                format_size(backup["size_bytes"]),
            ), iid=backup["path"])

    def get_selected_path():
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a backup first.")
            return None
        return selected  # iid was set to the full path above

    def handle_backup_now():
        try:
            path = create_backup()
            refresh()
            messagebox.showinfo("Success", f"Backup created:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def handle_restore():
        path = get_selected_path()
        if not path:
            return

        confirm = messagebox.askyesno(
            "Confirm Restore",
            "This will REPLACE all current data (sales, purchases, customers, "
            "everything) with the data from this backup.\n\n"
            "Your current database will first be saved as a safety copy, but "
            "anything entered after this backup was made will be lost.\n\n"
            "Are you sure you want to continue?",
            icon="warning"
        )
        if not confirm:
            return

        try:
            restore_backup(path)
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))
            return

        messagebox.showinfo(
            "Restore Complete",
            "The backup has been restored. Please close and reopen the app now "
            "for the restored data to take effect."
        )

    def handle_open_folder():
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        folder_path = os.path.abspath(BACKUP_FOLDER)
        if sys.platform == "win32":
            os.startfile(folder_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])

    # ---------------- Buttons ----------------
    button_frame = Frame(win, bg=BACKGROUND)
    button_frame.pack(fill=X, padx=20, pady=(0, 20))

    Button(
        button_frame, text="💾 Backup Now", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_backup_now
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="♻ Restore Selected", relief=FLAT, cursor="hand2",
        command=handle_restore
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="📂 Open Backups Folder", relief=FLAT, cursor="hand2",
        command=handle_open_folder
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    Button(
        button_frame, text="🔄 Refresh", relief=FLAT, cursor="hand2",
        command=refresh
    ).pack(side=LEFT, padx=5, ipadx=10, ipady=4)

    refresh()