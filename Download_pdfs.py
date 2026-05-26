import json
import time
import requests
from pathlib import Path
from tqdm import tqdm

PDF_DIR = Path("data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

with open("data/papers.json", "r", encoding="utf-8") as f:
    papers = json.load(f)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research bot; mailto:your@email.com)"
}

failed = []
skipped = 0
downloaded = 0

for paper in tqdm(papers, desc="Downloading PDFs"):
    paper_id = paper["id"]
    pdf_url = f"https://arxiv.org/pdf/{paper_id}"

    clean_id = paper_id.replace("/", "_")
    output_path = PDF_DIR / f"{clean_id}.pdf"

    if output_path.exists() and output_path.stat().st_size > 10_000:
        skipped += 1
        continue

    try:
        response = requests.get(pdf_url, headers=HEADERS, timeout=60, allow_redirects=True, stream=True)
        response.raise_for_status()

        first_chunk = b""
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not first_chunk:
                    first_chunk = chunk
                    if not first_chunk.startswith(b"%PDF"):
                        raise ValueError(f"Not a valid PDF — got: {first_chunk[:60]}")
                f.write(chunk)

        downloaded += 1
        time.sleep(1.5)

    except Exception as e:
        output_path.unlink(missing_ok=True)
        print(f"\n Failed {paper_id}: {e}")
        failed.append({"id": paper_id, "url": pdf_url, "error": str(e)})

if failed:
    with open("data/failed_downloads.json", "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)
    print(f"\n {len(failed)} failures saved to data/failed_downloads.json")

print(f"\n Downloaded: {downloaded} | Skipped: {skipped} | Failed: {len(failed)}")
print(f"  PDFs saved to: {PDF_DIR.resolve()}")