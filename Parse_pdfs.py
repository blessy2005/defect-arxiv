import fitz
import json
from pathlib import Path
from tqdm import tqdm

PDF_DIR = Path("data/pdfs")
OUTPUT_FILE = Path("data/parsed.json")

parsed_papers = []

pdf_files = list(PDF_DIR.glob("*.pdf"))

for pdf_path in tqdm(pdf_files):
    try:
        doc = fitz.open(pdf_path)

        full_text = ""

        for page in doc:
            text = page.get_text()
            full_text += text + "\n"
        parsed_papers.append({
            "id": pdf_path.stem,
            "pages": len(doc),
            "text": full_text[:120000]
        })

        print(f"Parsed: {pdf_path.name}")

    except Exception as e:
        print(f"Failed parsing {pdf_path.name}: {e}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(parsed_papers, f, indent=2, ensure_ascii=False)

print(f"\nSaved parsed data for {len(parsed_papers)} papers")