import json
import sys
import time
import requests
from pathlib import Path
from tqdm import tqdm

WORKERS_URL = "https://fabric.materials.wiki/workers"
API_URL = "https://fabric.materials.wiki/v1/chat/completions"

MODEL = "gpt-oss-20b"

OUTPUT_DIR = Path("summaries")
OUTPUT_DIR.mkdir(exist_ok=True)

FAILED_FILE = Path("data/failed_summaries.json")

HEADERS = {
    "Content-Type": "application/json"
}

failed_summaries = []

try:
    workers = requests.get(WORKERS_URL, timeout=30).json()

    if not workers.get("workers"):
        print("No active workers available.")
        sys.exit(1)

    available_models = []

    for worker in workers["workers"]:
        available_models.extend(worker.get("models", []))

    print(f"Workers available: {len(workers['workers'])}")
    print(f"Available models: {set(available_models)}")

    if MODEL not in available_models:
        print(f"Model '{MODEL}' is not currently available.")
        sys.exit(1)

except Exception as e:
    print(f"Worker check failed: {e}")
    sys.exit(1)


with open("data/parsed.json", "r", encoding="utf-8") as f:
    papers = json.load(f)


SYSTEM_PROMPT = """
You are a condensed matter physics and materials science research assistant.

Generate a high-quality markdown summary of the paper.

The summary should be technically precise, concise, and useful for literature review and retrieval.

Use EXACTLY this structure:

# Title

## Main Contribution
Provide 1-2 sentences describing the primary scientific contribution and why it matters.

## Research Problem
Describe the scientific problem or hypothesis.

## Methodology
Summarize:
- experimental methods
- computational methods
- simulations
- characterization techniques
- theoretical approaches

Keep this concise but technically specific.

## Key Findings
Provide the main scientific results as bullet points.
Preserve important numerical values when available.

## Materials/System
Describe:
- materials
- compositions
- substrates
- interfaces
- defects
- physical systems studied

## Defects Discussed
Summarize all defect-related concepts:
- vacancies
- dislocations
- impurities
- grain boundaries
- amorphous defects
- crack defects
- voids
- interface defects
etc.

Explain how the defects influence behavior or properties.

## Limitations
List limitations, assumptions, uncertainties, or unresolved questions.

## Keywords
Provide 5-15 concise scientific keywords.

Rules:
- Use markdown formatting.
- Be scientifically accurate.
- Do not invent results not present in the paper.
- Prefer concise technical writing over long explanations.
- Preserve important quantitative values.
"""

for paper in tqdm(papers, desc="Summarizing papers"):

    paper_id = paper["id"]
    text = paper["text"][:120000]

    output_path = OUTPUT_DIR / f"{paper_id}.md"

    if output_path.exists():
        continue

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    "Summarize this condensed matter/materials science paper:\n\n"
                    f"{text}"
                )
            }
        ],
        "temperature": 0.2
    }

    success = False

    for attempt in range(5):

        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                timeout=300
            )

            response.raise_for_status()

            data = response.json()

            if "choices" not in data:
                raise ValueError(f"Unexpected API response: {data}")

            summary = data["choices"][0]["message"]["content"]

            summary = f"""---
paper_id: {paper_id}
model: {MODEL}
---

{summary}
"""

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)

            print(f"Saved summary: {paper_id}")

            success = True
            time.sleep(2)

            break

        except Exception as e:
            print(f"Retry {attempt + 1} for {paper_id}: {e}")

            if attempt == 4:
                failed_summaries.append({
                    "paper_id": paper_id,
                    "error": str(e)
                })

            time.sleep(30)

    if not success:
        print(f"Failed permanently: {paper_id}")

if failed_summaries:

    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(failed_summaries, f, indent=2)

    print(f"\nSaved failures to {FAILED_FILE}")

print("\nSummarization complete.")