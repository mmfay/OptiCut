
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from collections import defaultdict
import csv

# ----------------------------
# FUNCTION: allocate_cuts_by_item_number
# ----------------------------
def allocate_cuts_by_item_number(reels, cuts):
    reels_by_item = defaultdict(list)
    for r in reels:
        r["remaining"] = r["length"]
        r["cuts"] = []
        reels_by_item[r["item_number"]].append(r)

    cuts_by_item = defaultdict(list)
    for c in cuts:
        cuts_by_item[c["item_number"]].append(c["length"])

    all_results = []
    all_unassigned = []

    for item_number, item_cuts in cuts_by_item.items():
        sorted_cuts = sorted(item_cuts, reverse=True)
        item_reels = reels_by_item.get(item_number, [])
        unassigned = []

        for cut in sorted_cuts:
            placed = False
            for reel in item_reels:
                if reel["remaining"] >= cut:
                    reel["cuts"].append(cut)
                    reel["remaining"] -= cut
                    placed = True
                    break
            if not placed:
                unassigned.append((cut, item_number))

        all_results.extend(item_reels)
        all_unassigned.extend(unassigned)

    return all_results, all_unassigned

# ----------------------------
# CLASS: WireOptimizerApp
# ----------------------------
class WireOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wire Reel Cut Optimizer")

        self.reels = []
        self.cuts = []
        self.optimized_result = []
        self.leftovers = []

        # Buttons
        tk.Button(root, text="Load Reels CSV", command=self.load_reels).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(root, text="Load Cuts CSV", command=self.load_cuts).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Optimize Cuts", command=self.optimize).grid(row=1, column=2, padx=5, pady=5)
        tk.Button(root, text="Export Assignments to CSV", command=self.export_assignments).grid(row=0, column=1, padx=5, pady=5)

        # Labels
        tk.Label(root, text="Reels").grid(row=2, column=0)
        tk.Label(root, text="Cuts").grid(row=2, column=1)
        tk.Label(root, text="Assignments").grid(row=2, column=2)

        # Reels Treeview
        self.reels_tree = self.create_treeview(root, ("Serial", "Item Number", "Length"), 25, 3, 0)

        # Cuts Treeview
        self.cuts_tree = self.create_treeview(root, ("Item Number", "Length"), 25, 3, 1)

        # Assignments Treeview
        self.assignments_tree = self.create_treeview(root, ("Serial", "Item Number", "Cut Length"), 25, 3, 2)

    def create_treeview(self, root, columns, height, row, column):
        tree = ttk.Treeview(root, columns=columns, show="headings", height=height)
        for col in columns:
            tree.heading(col, text=col, command=lambda c=col, t=tree: self.sort_treeview(t, c, False))
            tree.column(col, width=100)
        tree.grid(row=row, column=column, padx=5, pady=5)
        return tree

    def sort_treeview(self, tree, col, reverse):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)
        for index, (val, k) in enumerate(data):
            tree.move(k, "", index)
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))

    def load_reels(self):
        file_path = filedialog.askopenfilename()
        try:
            df = pd.read_csv(file_path)
            required_cols = {"serial", "length", "item_number"}
            if not required_cols.issubset(df.columns):
                raise ValueError("Missing required columns in Reels CSV (serial, length, item_number)")

            self.reels = df.to_dict(orient="records")
            for row in self.reels_tree.get_children():
                self.reels_tree.delete(row)

            for r in self.reels:
                self.reels_tree.insert("", tk.END, values=(r['serial'], r['item_number'], r['length']))

            messagebox.showinfo("Success", f"Loaded {len(self.reels)} reels.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load reels:\n{e}")

    def load_cuts(self):
        file_path = filedialog.askopenfilename()
        try:
            df = pd.read_csv(file_path)
            required_cols = {"length", "item_number"}
            if not required_cols.issubset(df.columns):
                raise ValueError("Missing required columns in Cuts CSV (length, item_number)")

            self.cuts = df.to_dict(orient="records")
            for row in self.cuts_tree.get_children():
                self.cuts_tree.delete(row)

            for c in self.cuts:
                self.cuts_tree.insert("", tk.END, values=(c['item_number'], c['length']))

            messagebox.showinfo("Success", f"Loaded {len(self.cuts)} cuts.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load cuts:\n{e}")

    def optimize(self):
        if not self.reels or not self.cuts:
            messagebox.showwarning("Missing Data", "Please load both reels and cuts.")
            return

        result, leftovers = allocate_cuts_by_item_number(self.reels.copy(), self.cuts)
        self.optimized_result = result
        self.leftovers = leftovers

        for tree in [self.assignments_tree, self.cuts_tree]:
            for row in tree.get_children():
                tree.delete(row)

        applied_cuts = {(reel["item_number"], cut) for reel in result for cut in reel["cuts"]}

        for c in self.cuts:
            tag = "green" if (c['item_number'], c['length']) in applied_cuts else "red"
            self.cuts_tree.insert("", tk.END, values=(c['item_number'], c['length']), tags=(tag,))
        self.cuts_tree.tag_configure("green", background="pale green")
        self.cuts_tree.tag_configure("red", background="#ff9999")

        for reel in result:
            for cut in reel["cuts"]:
                self.assignments_tree.insert("", tk.END, values=(reel["serial"], reel["item_number"], cut))

    def export_assignments(self):
        if not self.optimized_result:
            messagebox.showwarning("No Data", "Run optimization first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["item_number", "serial", "cut_length"])
                for reel in self.optimized_result:
                    for cut in reel["cuts"]:
                        writer.writerow([reel["item_number"], reel["serial"], cut])
            messagebox.showinfo("Success", f"Exported assignments to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

# ----------------------------
# MAIN ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = WireOptimizerApp(root)
    root.mainloop()
