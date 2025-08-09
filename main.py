import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from collections import defaultdict
import csv

def allocate_cuts_by_item_number(lengths, cuts):
    lengths_by_item = defaultdict(list)
    for r in lengths:
        r["remaining"] = r["length"]
        r["cuts"] = []
        lengths_by_item[r["item_number"]].append(r)

    cuts_by_item = defaultdict(list)
    for c in cuts:
        cuts_by_item[c["item_number"]].append(c["length"])

    all_results = []
    all_unassigned = []

    for item_number, item_cuts in cuts_by_item.items():
        sorted_cuts = sorted(item_cuts, reverse=True)
        item_lengths = lengths_by_item.get(item_number, [])
        unassigned = []

        for cut in sorted_cuts:
            placed = False
            for length in item_lengths:
                if length["remaining"] >= cut:
                    length["cuts"].append(cut)
                    length["remaining"] -= cut
                    placed = True
                    break
            if not placed:
                unassigned.append((cut, item_number))

        all_results.extend(item_lengths)
        all_unassigned.extend(unassigned)

    return all_results, all_unassigned

class OptiCutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OptiCut")

        self.lengths = []
        self.cuts = []
        self.optimized_result = []
        self.leftovers = []

        # Top buttons
        tk.Button(root, text="Load Lengths CSV", command=self.load_lengths).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(root, text="Load Cuts CSV", command=self.load_cuts).grid(row=0, column=1, padx=5, pady=5)

        # Labels
        tk.Label(root, text="Lengths").grid(row=1, column=0)
        tk.Label(root, text="Cuts").grid(row=1, column=1)

        # Lengths Treeview
        self.lengths_tree = self.create_treeview(root, ("Serial", "Item Number", "Length"), 25, 2, 0)

        # Cuts Treeview (with Serial column)
        self.cuts_tree = self.create_treeview(root, ("Item Number", "Length", "Serial"), 25, 2, 1)

        # Button frame beside Cuts grid
        button_frame = tk.Frame(root)
        button_frame.grid(row=2, column=2, sticky="n", padx=10)

        tk.Button(button_frame, text="Optimize Cuts", command=self.optimize, width=20).pack(pady=5)
        tk.Button(button_frame, text="Export Assignments to CSV", command=self.export_assignments, width=20).pack(pady=5)

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

    def load_lengths(self):
        file_path = filedialog.askopenfilename()
        try:
            df = pd.read_csv(file_path)
            required_cols = {"serial", "length", "item_number"}
            if not required_cols.issubset(df.columns):
                raise ValueError("Missing required columns in Lengths CSV (serial, length, item_number)")

            self.lengths = df.to_dict(orient="records")
            for row in self.lengths_tree.get_children():
                self.lengths_tree.delete(row)

            for r in self.lengths:
                self.lengths_tree.insert("", tk.END, values=(r['serial'], r['item_number'], r['length']))

            messagebox.showinfo("Success", f"Loaded {len(self.lengths)} lengths.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load lengths:\n{e}")

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
                self.cuts_tree.insert("", tk.END, values=(c['item_number'], c['length'], ""))

            messagebox.showinfo("Success", f"Loaded {len(self.cuts)} cuts.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load cuts:\n{e}")

    def optimize(self):
        if not self.lengths or not self.cuts:
            messagebox.showwarning("Missing Data", "Please load both lengths and cuts.")
            return

        result, leftovers = allocate_cuts_by_item_number(self.lengths.copy(), self.cuts)
        self.optimized_result = result
        self.leftovers = leftovers

        for row in self.cuts_tree.get_children():
            self.cuts_tree.delete(row)

        # Map (item_number, cut_length) to serials
        cut_serial_map = []
        for length in result:
            for cut in length["cuts"]:
                cut_serial_map.append((length["item_number"], cut, length["serial"]))

        used_serials = defaultdict(list)
        for item_num, cut_len, serial in cut_serial_map:
            used_serials[(item_num, cut_len)].append(serial)

        for c in self.cuts:
            key = (c['item_number'], c['length'])
            if key in used_serials and used_serials[key]:
                serial = used_serials[key].pop(0)
                tag = "green"
            else:
                serial = ""
                tag = "red"
            self.cuts_tree.insert("", tk.END, values=(c['item_number'], c['length'], serial), tags=(tag,))

        self.cuts_tree.tag_configure("green", background="pale green")
        self.cuts_tree.tag_configure("red", background="#ff9999")

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
                for length in self.optimized_result:
                    for cut in length["cuts"]:
                        writer.writerow([length["item_number"], length["serial"], cut])
            messagebox.showinfo("Success", f"Exported assignments to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

# ----------------------------
# MAIN ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = OptiCutApp(root)
    root.mainloop()
