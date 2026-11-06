"""Fetch real reference images used to check whether AI-image detectors work.

Real paintings: public-domain oil paintings dated 1860 to 1930 from the Art
Institute of Chicago's open collection (CC0 images), on subjects like the Set A
scenes. Real photographs: Wikimedia Commons "Quality images" on subjects like
the Set B scenes. These images are used only to test the detectors; participants
never see them. Writes model_comparison_2026-10-15/references/ and refs.csv.
"""

import csv
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "model_comparison_2026-10-15" / "references"
UA = {"User-Agent": "DGK-Lab research (davidgkamper@ucla.edu)", "AIC-User-Agent": "DGK-Lab research (davidgkamper@ucla.edu)"}

PAINTING_QUERIES = ["woman reading", "kitchen interior", "fisherman", "harbor boats", "children meadow", "violinist",
                    "market", "river boat", "still life bread", "snow village", "winter street", "garden bench",
                    "blossoming tree", "lighthouse", "stormy sea", "interior lamp"]
PHOTO_QUERIES = ["woman reading armchair", "bicycle repair", "raincoat street", "chef kitchen", "lemons bowl",
                 "canoe lake", "hallway chair", "street night rain", "cafe interior", "harbor boats",
                 "garden bench", "village street"]
N_EACH = 30


def fetch_paintings():
    seen, rows = set(), []
    for q in PAINTING_QUERIES:
        url = "https://api.artic.edu/api/v1/artworks/search"
        params = {"q": q, "limit": 40,
                  "fields": "id,title,artist_title,date_end,is_public_domain,artwork_type_title,image_id"}
        data = requests.get(url, params=params, headers=UA, timeout=60).json().get("data", [])
        for a in data:
            if (a.get("is_public_domain") and a.get("artwork_type_title") == "Painting" and a.get("image_id")
                    and a.get("date_end") and 1860 <= a["date_end"] <= 1930 and a["id"] not in seen):
                seen.add(a["id"])
                rows.append({"kind": "real_painting", "query": q, "source_id": a["id"], "title": a["title"],
                             "creator": a.get("artist_title") or "", "date": a["date_end"],
                             "url": f"https://www.artic.edu/iiif/2/{a['image_id']}/full/843,/0/default.jpg"})
                break_count = sum(r["query"] == q for r in rows)
                if break_count >= 2:
                    break
        time.sleep(1)
    return rows[:N_EACH]


def fetch_photos():
    seen, rows = set(), []
    api = "https://commons.wikimedia.org/w/api.php"
    for q in PHOTO_QUERIES:
        params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 10,
                  "gsrsearch": f"incategory:Quality_images filemime:image/jpeg {q}", "prop": "imageinfo",
                  "iiprop": "url|extmetadata", "iiurlwidth": 1024}
        pages = requests.get(api, params=params, headers=UA, timeout=60).json().get("query", {}).get("pages", {})
        for p in sorted(pages.values(), key=lambda x: x.get("index", 0))[:3]:
            info = p["imageinfo"][0]
            if p["title"] in seen:
                continue
            seen.add(p["title"])
            meta = info.get("extmetadata", {})
            rows.append({"kind": "real_photo", "query": q, "source_id": p["title"], "title": p["title"],
                         "creator": (meta.get("Artist", {}).get("value") or "")[:80],
                         "date": (meta.get("DateTimeOriginal", {}).get("value") or "")[:20],
                         "url": info.get("thumburl") or info["url"]})
        time.sleep(1)
    return rows[:N_EACH]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = fetch_paintings() + fetch_photos()
    kept = []
    for i, r in enumerate(rows):
        fn = f"{r['kind']}_{i:03d}.jpg"
        try:
            img = requests.get(r["url"], headers=UA, timeout=120)
            img.raise_for_status()
            (OUT / fn).write_bytes(img.content)
            r["file"] = fn
            kept.append(r)
        except Exception as e:
            print("skip", r["url"], e)
        time.sleep(0.5)
    with open(OUT / "refs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "kind", "query", "source_id", "title", "creator", "date", "url"])
        w.writeheader()
        w.writerows(kept)
    print(f"{sum(r['kind'] == 'real_painting' for r in kept)} paintings, "
          f"{sum(r['kind'] == 'real_photo' for r in kept)} photographs saved to {OUT}")


if __name__ == "__main__":
    main()
