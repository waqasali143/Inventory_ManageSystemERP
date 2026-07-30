from tkinter import messagebox
from datetime import date
from repositories import expense_repository as repo
from utils import event_bus


# =====================================
# Validation
# =====================================
def validate_expense_data(category, amount, expense_date_str):

    if category.get().strip() == "":
        return False, "Category is required."

    try:
        amount_value = float(amount.get())
    except ValueError:
        return False, "Invalid Amount."

    if amount_value <= 0:
        return False, "Amount must be greater than zero."

    value = expense_date_str.strip()
    if value == "":
        return True, ""

    try:
        date.fromisoformat(value)
    except ValueError:
        return False, "Expense Date must be in YYYY-MM-DD format."

    return True, ""

def resolve_expense_date(expense_date_str):
    value = expense_date_str.strip()
    if value == "":
        return date.today().isoformat()
    return value

# =====================================
# Load / Search
# =====================================
def load_expenses(search_term=None):
    return repo.fetch_expenses(search_term)

# =====================================
# Save Expense
# =====================================
def save_expense(category, description, amount, expense_date):

    is_valid, message = validate_expense_data(category, amount, expense_date.get())
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    repo.insert_expense(
        category.get().strip(),
        description.get().strip(),
        float(amount.get()),
        resolve_expense_date(expense_date.get())
    )
    event_bus.publish()

    messagebox.showinfo("Success", "Expense Added Successfully")
    return True

# =====================================
# Update Expense
# =====================================
def update_expense(selected_id, category, description, amount, expense_date):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select an expense first.")
        return False

    is_valid, message = validate_expense_data(category, amount, expense_date.get())
    if not is_valid:
        messagebox.showerror("Validation Error", message)
        return False

    repo.update_expense(
        selected_id.get(),
        category.get().strip(),
        description.get().strip(),
        float(amount.get()),
        resolve_expense_date(expense_date.get())
    )
    event_bus.publish()

    messagebox.showinfo("Success", "Expense Updated Successfully")
    return True
# =====================================
# Delete Expense
# =====================================
def delete_expense(selected_id):

    if not selected_id.get():
        messagebox.showerror("Error", "Please select an expense first.")
        return False

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this expense?"
    )
    if not confirm:
        return False

    repo.delete_expense(selected_id.get())

    event_bus.publish()

    messagebox.showinfo("Success", "Expense Deleted Successfully")
    return True