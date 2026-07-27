from tkinter import ttk, W


def build_treeview(parent, columns, height=None):
    """
    columns example:
        [{"key": "id", "heading": "ID", "width": 60, "anchor": CENTER}, ...]
    """
    keys = [col["key"] for col in columns]
    kwargs = {"columns": keys, "show": "headings"}
    if height:
        kwargs["height"] = height

    tree = ttk.Treeview(parent, **kwargs)

    for col in columns:
        tree.heading(col["key"], text=col["heading"])
        tree.column(
            col["key"],
            width=col.get("width", 100),
            anchor=col.get("anchor", W)
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