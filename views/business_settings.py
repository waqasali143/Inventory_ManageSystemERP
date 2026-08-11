from tkinter import *
from tkinter import messagebox
from services.tax_service import get_filer_tax_rate, get_non_filer_tax_rate, set_tax_rates
from services.settings_service import get_business_info, save_business_info
from utils.theme import (
    PRIMARY, BACKGROUND, WHITE,
    FONT_TITLE, FONT_BODY_BOLD,
    apply_app_style
)
from utils.ui_helpers import labeled_entry
from utils.window_helpers import size_and_center
from utils.branding_helpers import add_branding_strip

# ======================================================================

def open_window():

    win = Toplevel()
    add_branding_strip(win)

    win.title("Business Settings")
    win.configure(bg=BACKGROUND)

    size_and_center(win, width_ratio=0.4, height_ratio=0.55, resizable=False)

    apply_app_style()

    # ---------------- Header ----------------
    header_frame = Frame(win, bg=PRIMARY, height=60)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(False)

    Label(
        header_frame, text="BUSINESS SETTINGS",
        bg=PRIMARY, fg=WHITE, font=FONT_TITLE
    ).pack(side=LEFT, padx=20)

    # ---------------- Form ----------------
    form_frame = LabelFrame(
        win, text="Invoice Letterhead Info", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    form_frame.pack(fill="x", padx=20, pady=20)
    form_frame.columnconfigure(1, weight=1)

    current = get_business_info()

    name = StringVar(value=current["name"])
    address = StringVar(value=current["address"])
    phone = StringVar(value=current["phone"])
    ntn = StringVar(value=current["ntn"])

    labeled_entry(form_frame, "Business Name (Licensed)", 0, 0, name, justify="left", readonly=True)    
    labeled_entry(form_frame, "Address", 1, 0, address, justify="left")
    labeled_entry(form_frame, "Phone", 2, 0, phone, justify="left")
    labeled_entry(form_frame, "NTN (optional)", 3, 0, ntn, justify="left")

    def handle_save():
        save_business_info(address.get().strip(), phone.get().strip(), ntn.get().strip())
        messagebox.showinfo("Success", "Business Settings Saved")

    Button(
        form_frame, text="💾 Save Settings", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_save
    ).grid(row=4, column=0, columnspan=2, pady=15, sticky="ew", padx=10, ipady=6)
    # ===================================================================================
    # ---------------- Tax Rates ----------------
    tax_frame = LabelFrame(
        win, text="Filer / Non-Filer Tax Rates (%)", bg=BACKGROUND,
        font=FONT_BODY_BOLD, padx=10, pady=10
    )
    tax_frame.pack(fill="x", padx=20, pady=(0, 20))
    tax_frame.columnconfigure(1, weight=1)

    filer_rate = StringVar(value=str(get_filer_tax_rate()))
    non_filer_rate = StringVar(value=str(get_non_filer_tax_rate()))

    labeled_entry(tax_frame, "Filer Tax %", 0, 0, filer_rate, justify="left")
    labeled_entry(tax_frame, "Non-Filer Tax %", 1, 0, non_filer_rate, justify="left")

    def handle_save_tax_rates():
        try:
            f_rate = float(filer_rate.get())
            nf_rate = float(non_filer_rate.get())
        except ValueError:
            messagebox.showerror("Error", "Tax rates must be numbers.")
            return

        set_tax_rates(f_rate, nf_rate)
        messagebox.showinfo("Success", "Tax rates updated.")

    Button(
        tax_frame, text="💾 Save Tax Rates", bg=PRIMARY, fg=WHITE,
        relief=FLAT, cursor="hand2", command=handle_save_tax_rates
    ).grid(row=2, column=0, columnspan=2, pady=15, sticky="ew", padx=10, ipady=6)