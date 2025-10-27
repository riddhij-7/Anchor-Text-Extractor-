import requests
from bs4 import BeautifulSoup
import csv
import threading
from concurrent.futures import ThreadPoolExecutor
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from PIL import Image

# --- CONFIGURATION (Default Values for GUI) ---
DEFAULT_DOMAIN = "digitalfarm.ae"
DEFAULT_THREADS = 8
REQUEST_TIMEOUT = 15

# Global variable to store the path to the input URLs file
input_file_path = None

# --- CORE EXTRACTION LOGIC ---

def fetch_anchor_texts(url, domain):
    """Fetches anchor texts from a single URL linking to the specified domain."""
    results = []
    try:
        # Use a standard User-Agent header
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"}, timeout=REQUEST_TIMEOUT)
        
        # Handle non-200 status codes
        if response.status_code != 200:
            results.append((url, "", "", "", f"Failed ({response.status_code})"))
            return results

        soup = BeautifulSoup(response.text, "html.parser")
        anchors = soup.find_all("a", href=True)

        found_links = False
        for a in anchors:
            href = a.get("href")
            # Check if the domain is present in the link's href
            if href and domain in href:
                text = a.get_text(strip=True)
                rel = (a.get("rel") or [])
                rel = [r.lower() for r in rel]
                nofollow = "nofollow" in rel
                link_type = "NoFollow" if nofollow else "DoFollow"
                results.append((url, text, href, link_type, "Success"))
                found_links = True

        # Record if no links matching the domain were found on the page
        if not found_links:
            results.append((url, "", "", "", "No link found"))

    except requests.exceptions.Timeout:
        results.append((url, "", "", "", "Error: Request timed out"))
    except requests.exceptions.RequestException as e:
        # Catch network errors, SSL errors, etc.
        error_msg = str(e).split('\n')[0] # Get only the first line of the error
        results.append((url, "", "", "", f"Error: {error_msg[:60]}"))
    except Exception as e:
        results.append((url, "", "", "", f"Unexpected Error: {str(e)[:60]}"))
        
    return results

def run_extraction_worker(app_instance, urls, domain, max_threads, output_file_path):
    """
    Main extraction function called in a separate thread.
    Handles the concurrency and updates the GUI via the main thread.
    """
    total_urls = len(urls)
    
    # Check for empty URL list
    if total_urls == 0:
        app_instance.after(0, lambda: app_instance.update_status("🚨 No URLs found in the file.", False))
        app_instance.after(0, lambda: app_instance.toggle_running_state(False))
        return

    # Prepare for output
    try:
        with open(output_file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Referring URL", "Anchor Text", "Link URL", "Link Type", "Status"])

            app_instance.after(0, lambda: app_instance.update_status(f"🚀 Starting extraction of {total_urls} URLs...", True))
            
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit all tasks
                future_to_url = {executor.submit(fetch_anchor_texts, url, domain): url for url in urls}

                completed_count = 0
                for future in future_to_url:
                    # Check if the process should be cancelled
                    if not app_instance.running:
                        break
                        
                    url = future_to_url[future]
                    try:
                        results = future.result()
                        # Write results immediately
                        writer.writerows(results)
                    except Exception as e:
                        # Handle unexpected thread-level errors
                        error_msg = f"Thread error for {url}: {str(e)[:50]}"
                        app_instance.after(0, lambda: print(error_msg)) # Log to console
                        writer.writerow([url, "", "", "", error_msg])

                    completed_count += 1
                    progress_value = completed_count / total_urls

                    # Update GUI in the main thread
                    app_instance.after(0, lambda: app_instance.update_progress(
                        progress_value, f"[{completed_count}/{total_urls}] Done: {url}"
                    ))
            
            # --- Final completion logic ---
            if app_instance.running:
                final_message = f"✅ Completed! Results saved to: {output_file_path}"
                app_instance.after(0, lambda: app_instance.update_status(final_message, False))
            else:
                # If loop was broken due to cancellation
                final_message = f"🛑 Cancelled. Processed {completed_count}/{total_urls} URLs."
                app_instance.after(0, lambda: app_instance.update_status(final_message, False))


    except PermissionError:
        app_instance.after(0, lambda: app_instance.update_status(f"❌ Error: Cannot write to output file. Check permissions or if the file is open.", False))
    except Exception as e:
        app_instance.after(0, lambda: app_instance.update_status(f"❌ An unexpected file error occurred: {str(e)[:80]}", False))
        
    finally:
        app_instance.after(0, lambda: app_instance.toggle_running_state(False))


# --- GUI APPLICATION CLASS ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Setup Window ---
        self.title("Anchor Text Link Extractor (v1.0)")
        self.geometry("600x480")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=0)

        # State management
        self.running = False
        self.input_file_path = ""
        self.output_file_path = ""
        self.worker_thread = None

        # --- Load Icon (Using a simple SVG-like representation via text, as PyInstaller can struggle with image files)
        # Using a simple label for "icon" aesthetic
        self.title_label = ctk.CTkLabel(self, text="🔗 Anchor Text Analyzer", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # --- Configuration Frame ---
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure((0, 1), weight=1)

        # Domain Input
        ctk.CTkLabel(self.config_frame, text="Target Domain (e.g., google.com):").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.domain_entry = ctk.CTkEntry(self.config_frame, placeholder_text=DEFAULT_DOMAIN)
        self.domain_entry.insert(0, DEFAULT_DOMAIN)
        self.domain_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Threads Input
        ctk.CTkLabel(self.config_frame, text=f"Max Concurrent Threads (1-{DEFAULT_THREADS*2}):").grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
        self.thread_slider = ctk.CTkSlider(self.config_frame, from_=1, to=DEFAULT_THREADS*2, number_of_steps=(DEFAULT_THREADS*2)-1, command=self.update_thread_label)
        self.thread_slider.set(DEFAULT_THREADS)
        self.thread_slider.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")
        self.thread_label = ctk.CTkLabel(self.config_frame, text=f"Threads: {DEFAULT_THREADS}")
        self.thread_label.grid(row=2, column=1, padx=10, pady=(0, 5), sticky="w")

        # --- File Selection Frame ---
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.file_frame.grid_columnconfigure((0, 1), weight=1)

        # Input File Selection
        self.input_path_label = ctk.CTkLabel(self.file_frame, text="Input URLs File: (Not selected)", wraplength=250)
        self.input_path_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.select_input_btn = ctk.CTkButton(self.file_frame, text="Select URL File", command=self.select_input_file)
        self.select_input_btn.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # --- Progress and Run Frame ---
        self.run_frame = ctk.CTkFrame(self)
        self.run_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.run_frame.grid_columnconfigure((0, 1), weight=1)

        # Run Button
        self.run_button = ctk.CTkButton(self.run_frame, text="🚀 Start Extraction", command=self.start_extraction, fg_color="green")
        self.run_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Cancel Button (Hidden initially)
        self.cancel_button = ctk.CTkButton(self.run_frame, text="🛑 Cancel", command=self.cancel_extraction, fg_color="red")
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.cancel_button.grid_remove() # Hide initially

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.progress_bar.set(0)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Ready. Select input file and press Start.", wraplength=550)
        self.status_label.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="ew")


    # --- GUI METHODS ---

    def update_thread_label(self, value):
        """Updates the thread label dynamically with slider value."""
        self.thread_label.configure(text=f"Threads: {int(value)}")

    def update_status(self, message, is_running):
        """Updates the status label and progress bar mode."""
        self.status_label.configure(text=message)
        if is_running:
            # Set to indeterminate mode if starting a long operation
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            # Set to determinate mode and reset to 100% when finished/stopped
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0 if not self.running else 0.0) # Set to 100% on success

    def update_progress(self, progress_value, message):
        """Updates the progress bar and status label during extraction."""
        self.progress_bar.set(progress_value)
        self.status_label.configure(text=message)
        # Ensure the progress bar is in determinate mode now that we have a value
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.stop() # Stop the indeterminate movement

    def toggle_running_state(self, is_running):
        """Switches the UI state between running and idle."""
        self.running = is_running
        if is_running:
            self.run_button.grid_remove()
            self.cancel_button.grid()
            self.domain_entry.configure(state="disabled")
            self.thread_slider.configure(state="disabled")
            self.select_input_btn.configure(state="disabled")
        else:
            self.run_button.grid()
            self.cancel_button.grid_remove()
            self.domain_entry.configure(state="normal")
            self.thread_slider.configure(state="normal")
            self.select_input_btn.configure(state="normal")

    def select_input_file(self):
        """Opens a file dialog to select the input URL file."""
        # Use existing input_file_path if available, otherwise default to home directory
        initial_dir = os.path.dirname(self.input_file_path) if self.input_file_path else os.path.expanduser("~")
        
        filepath = filedialog.askopenfilename(
            title="Select Input URLs File",
            initialdir=initial_dir,
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if filepath:
            self.input_file_path = filepath
            # Display only the filename in the label for cleanliness
            display_name = os.path.basename(filepath)
            self.input_path_label.configure(text=f"Input URLs File: {display_name}")
            self.update_status("Input file selected. Ready to run.", False)

    def start_extraction(self):
        """Validates inputs and starts the extraction process in a new thread."""
        if not self.input_file_path or not os.path.exists(self.input_file_path):
            messagebox.showerror("Error", "Please select a valid input URLs file (.txt).")
            return

        domain = self.domain_entry.get().strip()
        if not domain:
            messagebox.showerror("Error", "Please enter a target domain.")
            return

        # Sanitize domain input (remove http/https and trailing slashes)
        domain = domain.replace('http://', '').replace('https://', '').strip('/')

        max_threads = int(self.thread_slider.get())

        # 1. Ask user for output file location
        default_output_name = f"anchor_texts_{domain.replace('.', '_')}_results.csv"
        self.output_file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_output_name,
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            title="Save Output CSV File"
        )

        if not self.output_file_path:
            self.update_status("Operation cancelled. Output file not selected.", False)
            return

        # 2. Read URLs from the input file
        try:
            with open(self.input_file_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f.readlines() if line.strip() and (line.strip().startswith('http') or line.strip().startswith('https'))]
        except Exception as e:
            messagebox.showerror("Error reading file", f"Could not read URLs from the file: {e}")
            return
            
        # 3. Start the worker thread
        self.toggle_running_state(True)
        # Create a non-daemon thread to prevent premature exit if the GUI closes
        self.worker_thread = threading.Thread(
            target=run_extraction_worker, 
            args=(self, urls, domain, max_threads, self.output_file_path)
        )
        self.worker_thread.start()

    def cancel_extraction(self):
        """Sets the flag to stop the worker thread gracefully."""
        if self.running:
            self.running = False
            self.update_status("🛑 Attempting to cancel... Please wait for current requests to finish.", False)
            # Worker thread handles the cleanup and setting the final state


if __name__ == "__main__":
    # Configure CustomTkinter appearance
    ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
    ctk.set_default_color_theme("blue") # Themes: "blue", "dark-blue", "green"

    app = App()
    app.mainloop()
