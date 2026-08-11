# =====================================================================
# Single source of truth for where the database file lives.
#
# For a single PC, leave this as the default relative path.
#
# For multiple PCs sharing one database (Admin's PC + 1-2 Cashier
# PCs), change DB_PATH on the OTHER PCs to a network path pointing
# at the Admin PC's shared folder, e.g.:
#
#     DB_PATH = r"\\ADMIN-PC\SharedInventory\inventory.db"
#
# The Admin's own PC (where the real file lives) keeps the default.
# =====================================================================

DB_PATH = "database/inventory.db"