import arxiv
import json
from pathlib import Path

OUTPUT = Path("data/papers.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

client = arxiv.Client(
    page_size=100,
    delay_seconds=3,
    num_retries=3
)

search = arxiv.Search(
    query='all:defect AND cat:cond-mat*',
    max_results=100,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

papers = []

for result in client.results(search):
    papers.append({
        "id": result.get_short_id().split("v")[0],
        "title": result.title,
        "authors": [a.name for a in result.authors],
        "abstract": result.summary,
        "published": str(result.published),
        "updated": str(result.updated),
        "categories": result.categories,
        "pdf_url": result.pdf_url,
        "arxiv_url": result.entry_id,
    })

    print(
        f"[{len(papers):>3}] "
        f"{result.get_short_id()} — "
        f"{result.title[:60]}"
    )

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(papers, f, indent=2, ensure_ascii=False)

print(f"\n Saved {len(papers)} papers to {OUTPUT}")