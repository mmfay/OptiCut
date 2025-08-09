# OptiCut

**OptiCut** is a length-based material cutting optimizer designed to minimize waste and maximize efficiency.  
Whether you're working with **wire, cable, metal pipes, wooden boards, fabric rolls, or any other material sold in lengths**, OptiCut calculates the most efficient cut plan for your job.


## ✨ Features
- **Multi-material support** — works with any length-based material.
- **Waste minimization** — optimizes cut patterns to reduce leftover scrap.
- **Batch job processing** — handle multiple orders or projects in a single run.
- **Custom input data** — easily load jobs from CSV or enter them directly in the UI.
- **Fast calculations** — optimization algorithm runs locally on your machine.
- **Offline, standalone tool** — no cloud connection required.


## 💡 Example Use Cases
- **Manufacturing** — cutting steel rods, pipes, or profiles.
- **Construction** — optimizing wood beams, studs, or trim pieces.
- **Electrical** — planning cable/wire cuts with minimal waste.
- **Textiles** — reducing scrap in fabric rolls.
- **Glass & Plastics** — optimizing sheets and tubes.


## 🖥 Requirements
- Python 3.7+
- pip (Python package manager)


## 📦 Installation

1. Install pandas:
```bash
pip install pandas
```

2. If you get a tkinter error, install it with
```bash
sudo apt-get install python3-tk
```


## ▶ Executing
Once Installed, you can run the following command,
```bash
python3 main.py
```

## 📦 Building
If an executable is needed, run the following, 
```bash
pyinstaller --onefile --windowed main.py
```

## 📄 License
Licensed under the [MIT License](LICENSE) © 2025 Matthew Fay (softwarerror)
