import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from collections import defaultdict
import csv  # ✅ Needed for export functionality

# ----------------------------
# FUNCTION: allocate_cuts_by_item_number
# ----------------------------
# This function performs the core logic.
# It matches wire cuts to wire reels, grouped by item_number.
# Each cut must be placed on a reel of the same item_number,
# and each reel has limited remaining length.
def allocate_cuts_by_item_number(reels, cuts):
    reels_by_item = defaultdict(list)  # Group reels by item_number

    # Prepare reel state: add remaining length and empty list of cuts
    for r in reels:
        r["remaining"] = r["length"]
        r["cuts"] = []
        reels_by_item[r["item_number"]].append(r)

    # Group cuts by item_number
    cuts_by_item = defaultdict(list)
    for c in cuts:
        cuts_by_item[c["item_number"]].append(c["length"])

    all_results = []      # All updated reels (with cuts assigned)
    all_unassigned = []   # Cuts that couldn't be assigned to a reel

    # Go through each item group independently
    for item_number, item_cuts in cuts_by_item.items():
        sorted_cuts = sorted(item_cuts, reverse=True)  # Greedy: largest cuts first
        item_reels = reels_by_item.get(item_number, [])
        unassigned = []

        # Try placing each cut into the first reel with enough space
        for cut in sorted_cuts:
            placed = False
            for reel in item_reels:
                if reel["remaining"] >= cut:
                    reel["cuts"].append(cut)
                    reel["remaining"] -= cut
                    placed = True
                    break
            if not placed:
                unassigned.append((cut, item_number))  # Track unassigned cuts

        all_results.extend(item_reels)        # Add updated reels to result list
        all_unassigned.extend(unassigned)     # Add leftover cuts

    return all_results, all_unassigned


# ----------------------------
# CLASS: WireOptimizerApp
# ----------------------------
# Main application class for the wire optimization GUI.
# Handles UI creation, file loading, and result display.
class WireOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wire Reel Cut Optimizer")

        self.reels = []  # Holds reel data after loading CSV
        self.cuts = []   # Holds cut data after loading CSV
        self.optimized_result = []  # ✅ Stores the result for exporting

        # Create top buttons for user actions
        tk.Button(root, text="Load Reels CSV", command=self.load_reels).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(root, text="Load Cuts CSV", command=self.load_cuts).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Optimize Cuts", command=self.optimize).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(root, text="Export Assignments to CSV", command=self.export_assignments).grid(row=0, column=3, padx=5, pady=5)

        # Add column labels above output areas
        tk.Label(root, text="Reels").grid(row=1, column=0)
        tk.Label(root, text="Cuts").grid(row=1, column=1)
        tk.Label(root, text="Assignments").grid(row=1, column=2)

        # Create 3 side-by-side Text widgets for output display
        self.reels_output = tk.Text(root, width=40, height=25)
        self.reels_output.grid(row=2, column=0, padx=5, pady=5)

        self.cuts_output = tk.Text(root, width=40, height=25)
        self.cuts_output.grid(row=2, column=1, padx=5, pady=5)

        self.assign_output = tk.Text(root, width=60, height=25)
        self.assign_output.grid(row=2, column=2, padx=5, pady=5)

    # ------------------------
    # LOAD REELS CSV
    # ------------------------
    def load_reels(self):
        file_path = filedialog.askopenfilename()
        try:
            df = pd.read_csv(file_path)
            required_cols = {"serial", "length", "item_number"}
            if not required_cols.issubset(df.columns):
                raise ValueError("Missing required columns in Reels CSV (serial, length, item_number)")

            self.reels = df.to_dict(orient="records")

            self.reels_output.delete(1.0, tk.END)
            for r in self.reels:
                self.reels_output.insert(
                    tk.END, f"{r['serial']} - {r['length']} (Item {r['item_number']})\n"
                )

            messagebox.showinfo("Success", f"Loaded {len(self.reels)} reels.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load reels:\n{e}")

    # ------------------------
    # LOAD CUTS CSV
    # ------------------------
    def load_cuts(self):
        file_path = filedialog.askopenfilename()
        try:
            df = pd.read_csv(file_path)
            required_cols = {"length", "item_number"}
            if not required_cols.issubset(df.columns):
                raise ValueError("Missing required columns in Cuts CSV (length, item_number)")

            self.cuts = df.to_dict(orient="records")

            self.cuts_output.delete(1.0, tk.END)
            for c in self.cuts:
                self.cuts_output.insert(
                    tk.END, f"{c['length']} (Item {c['item_number']})\n"
                )

            messagebox.showinfo("Success", f"Loaded {len(self.cuts)} cuts.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load cuts:\n{e}")

    # ------------------------
    # OPTIMIZE CUTS
    # ------------------------
    def optimize(self):
        if not self.reels or not self.cuts:
            messagebox.showwarning("Missing Data", "Please load both reels and cuts.")
            return

        # Run allocation function with fresh copy
        result, leftovers = allocate_cuts_by_item_number(self.reels.copy(), self.cuts)
        self.optimized_result = result  # ✅ Save result for export

        self.assign_output.delete(1.0, tk.END)

        for reel in result:
            cuts_str = ", ".join(str(c) for c in reel["cuts"])
            self.assign_output.insert(
                tk.END,
                f"{reel['serial']} (Item {reel['item_number']}) -> [{cuts_str}] | Remaining: {reel['remaining']}\n"
            )

        if leftovers:
            self.assign_output.insert(tk.END, "\nUnassigned Cuts:\n")
            for cut, item in leftovers:
                self.assign_output.insert(tk.END, f"{cut} (Item {item})\n")

    # ------------------------
    # EXPORT RESULTS TO CSV
    # ------------------------
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
