Anchor Text Link Extractor v1.0

This application allows quick and concurrent analysis of a list of URLs to find internal anchor texts pointing to a specified target domain.

How to Use

The tool is a standalone executable (.exe) and does not require any installation of Python or special libraries.

1. Configure Settings

Target Domain: Enter the domain you are trying to find links to (e.g., digitalfarm.ae). The tool will only track links on the input pages that point to this domain.

Max Concurrent Threads: Use the slider to set the number of parallel connections. The default of 8 is safe for most networks. Higher numbers run faster but may risk timeouts or temporary blocks from the sites being crawled.

2. Select Files

Select URL File: Click the button and choose the input file. This file must be a plain text file (.txt) where each URL you want to crawl is on a new line.

Start Extraction: Click the 🚀 Start Extraction button.

Save Output CSV: A "Save File" dialog will immediately appear. Choose a location and name for your output CSV file. This file will contain all the results.

3. Monitoring and Completion

The Progress Bar and Status Label will update in real-time, showing which URL is currently being processed and the overall completion status.

The 🛑 Cancel button appears while running, allowing you to stop the process gracefully at any time.

Once completed, the status will show the final message: ✅ Completed! Results saved to: [Your Output Path].
