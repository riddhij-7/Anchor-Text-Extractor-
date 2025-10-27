Anchor Text Link Extractor v1.0

Anchor Text Link Extractor v1.0 is a desktop application that allows quick and concurrent analysis of multiple URLs to find anchor texts pointing to a specific target domain.

Ideal for SEO specialists, web analysts, and developers who want to understand how their domain is being linked across various web pages.

🚀 Features

Concurrent Crawling – Analyze multiple URLs simultaneously with configurable threading.

Domain-Based Filtering – Extract only links pointing to your chosen domain.

Real-Time Progress Tracking – Watch live updates on progress and status.

Graceful Cancellation – Stop the process anytime safely.

CSV Export – Automatically saves clean, structured results in .csv format.

🧩 How to Use
1️⃣ Configure Settings

Target Domain: Enter the domain you want to track (e.g., digitalfarm.ae).
Only links pointing to this domain will be extracted.

Max Concurrent Threads:
Use the slider to adjust the number of parallel connections.

Default: 8 (recommended)

2️⃣ Select Files

Select URL File:
Choose a .txt file containing the list of URLs (one per line).

Start Extraction:
Click the 🚀 Start Extraction button.
A "Save File" dialog will appear — select the path and name for your output .csv file.

3️⃣ Monitor Progress

The progress bar and status label update in real-time.

The 🛑 Cancel button appears during processing — click it anytime to stop.

When finished, you’ll see:
✅ Completed! Results saved to: [Your Output Path]

👨‍💻 For Developers
🧱 Installation

Clone this repository and install dependencies:

```bash 
pip install -r requirements.txt
```

▶️ Run from Source

To launch the GUI:
```bash 
python3 anchor_text_gui.py
```
🏗️ Build Executable (.exe)

To package the app into a single executable file:

1️⃣ Install PyInstaller
```bash
pip install pyinstaller
```

2️⃣ Build Command
```bash
python -m PyInstaller --onefile --windowed --hidden-import=customtkinter anchor_text_gui.py
```
3️⃣ Locate Output

The built file will be located inside the /dist folder as:
```bash
anchor_text_gui.exe
```
📦 Output Format

The exported .csv file contains:

Column	Description
Source URL	The page URL where the anchor was found
Anchor Text	The clickable text of the link
Anchor Link	The full target URL of the link
Link Type	Internal or external
🧠 Notes

Ensure all URLs in the input file are valid and accessible.

This tool is intended for ethical and authorized use only.
