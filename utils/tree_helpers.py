from tkinter import ttk, W


def build_treeview(parent, columns, height=None):
    """
    Professional reusable Treeview builder.

    Column options:
        key
        heading
        width
        min_width
        anchor

    Example:
        {
            "key": "purchase_no",
            "heading": "Purchase No",
            "width": 105,
            "min_width": 90,
            "anchor": "center"
        }
    """

    keys = [col["key"] for col in columns]

    kwargs = {
        "columns": keys,
        "show": "headings"
    }

    if height:
        kwargs["height"] = height

    tree = ttk.Treeview(parent, **kwargs)

    for col in columns:

        key = col["key"]

        tree.heading(
            key,
            text=col["heading"]
        )

        tree.column(
            key,
            width=col.get("width", 100),
            minwidth=col.get(
                "min_width",
                col.get("width", 100)
            ),
            anchor=col.get("anchor", W),
            stretch=True
        )

    return tree


def clear_treeview(tree):
    for row in tree.get_children():
        tree.delete(row)


def fill_treeview(tree, rows):
    for row in rows:
        tree.insert("", "end", values=row)


def reload_treeview(tree, rows):
    clear_treeview(tree)
    fill_treeview(tree, rows)