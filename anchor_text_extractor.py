import requests
from bs4 import BeautifulSoup
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CONFIGURATION ===
DOMAIN = "digitalfarm.ae"       # <-- change this to your site
INPUT_FILE = "urls.txt"
OUTPUT_FILE = "anchor_texts.csv"
MAX_THREADS = 8                 # adjust: 5–10 threads is safe
REQUEST_TIMEOUT = 15

# === FUNCTION TO PROCESS A SINGLE URL ===
def fetch_anchor_texts(url, domain):
    results = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            results.append((url, "", "", "", f"Failed ({response.status_code})"))
            return results

        soup = BeautifulSoup(response.text, "html.parser")
        anchors = soup.find_all("a", href=True)

        found = False
        for a in anchors:
            href = a["href"]
            if domain in href:
                text = a.get_text(strip=True)
                rel = (a.get("rel") or [])
                rel = [r.lower() for r in rel]
                nofollow = "nofollow" in rel
                link_type = "NoFollow" if nofollow else "DoFollow"
                results.append((url, text, href, link_type, "Success"))
                found = True

        if not found:
            results.append((url, "", "", "", "No link found"))

    except Exception as e:
        results.append((url, "", "", "", f"Error: {str(e)[:60]}"))
    return results


# === MAIN EXECUTION ===
def main():
    with open(INPUT_FILE, "r") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Referring URL", "Anchor Text", "Link URL", "Link Type", "Status"])

        total = len(urls)
        print(f"Processing {total} URLs using {MAX_THREADS} threads...")

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            future_to_url = {executor.submit(fetch_anchor_texts, url, DOMAIN): url for url in urls}

            completed = 0
            for future in as_completed(future_to_url):
                completed += 1
                url = future_to_url[future]
                try:
                    results = future.result()
                    writer.writerows(results)
                except Exception as e:
                    writer.writerow([url, "", "", "", f"Thread error: {str(e)[:60]}"])

                print(f"[{completed}/{total}] Done: {url}")

    print("✅ Completed. Results saved to", OUTPUT_FILE)


if __name__ == "__main__":
    main()
