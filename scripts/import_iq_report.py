"""Parse the BD onboarding HTML into seed_modules.json.

Usage:
    python scripts/import_iq_report.py <path/to/bd-onboarding.html>

Structure consumed:
    [data-vertical-section]   -> vertical (hbw/ttd/fd/ha)
      [data-week-section]     -> week number
        [data-panel]          -> day number
          <h2>                -> day theme (module title)
          .stage / .res-card  -> lessons (one per res-card)

Each lesson keeps the res-card's inner HTML as content_body so embedded
Drive videos, slides, knowledge-check <details>, and link-pills survive.
The original <style> block is pulled out once as `lesson_css` so the
Streamlit lesson page can prepend it when rendering.
"""

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

VERTICAL_LABELS = {
    "hbw": "Health, Beauty & Wellness",
    "ttd": "Things To Do",
    "fd": "Food & Drink",
    "ha": "Home & Auto",
}


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "item"


def first_url(card_html: str) -> str | None:
    soup = BeautifulSoup(card_html, "html.parser")
    a = soup.find("a", href=True)
    if a and a["href"].startswith(("http://", "https://")):
        return a["href"]
    iframe = soup.find("iframe", src=True)
    if iframe:
        return iframe["src"]
    return None


def lesson_title(card) -> str:
    for tag in ("h4", "h3"):
        h = card.find(tag)
        if h and h.get_text(strip=True):
            return h.get_text(strip=True)
    return "Untitled lesson"


def parse(html_path: Path) -> dict:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    style = soup.find("style")
    lesson_css = style.string if style and style.string else ""

    modules = []
    seen_module_slugs = set()
    seen_lesson_slugs: dict[str, set] = {}

    display_order = 0

    for vert_div in soup.select("[data-vertical-section]"):
        vert_key = vert_div["data-vertical-section"]
        vert_label = VERTICAL_LABELS.get(vert_key, vert_key.upper())

        for week_div in vert_div.select("[data-week-section]"):
            week_num = int(week_div["data-week-section"])

            for day_panel in week_div.select("[data-panel]"):
                day_num = int(day_panel["data-panel"])

                h2 = day_panel.find("h2")
                day_theme = h2.get_text(strip=True) if h2 else f"Day {day_num}"

                module_title = f"Week {week_num} · Day {day_num} — {day_theme}"
                module_slug = slugify(f"{vert_key}-w{week_num}-d{day_num}-{day_theme}")
                if module_slug in seen_module_slugs:
                    module_slug = f"{module_slug}-{display_order}"
                seen_module_slugs.add(module_slug)
                seen_lesson_slugs[module_slug] = set()

                display_order += 1
                # Sort key: vertical group (stable), then week, then day.
                # Verticals share the same week/day numbering, so include vertical_idx
                # so HBW Week 1 Day 1 sorts before TTD Week 1 Day 1.
                vert_idx = list(VERTICAL_LABELS.keys()).index(vert_key)
                sort_key = vert_idx * 10000 + week_num * 100 + day_num
                module = {
                    "slug": module_slug,
                    "title": module_title,
                    "description": None,
                    "display_order": sort_key,
                    "week_target": week_num,
                    "vertical": vert_key,
                    "lessons": [],
                }

                # Iterate stages; each stage groups a set of res-cards.
                stages = day_panel.select("div.stage")
                cards = []
                if stages:
                    for stage in stages:
                        stage_h3 = stage.find("h3")
                        stage_label = stage_h3.get_text(strip=True) if stage_h3 else None
                        for card in stage.select("div.res-card"):
                            cards.append((stage_label, card))
                else:
                    # fall back: any res-card in the panel
                    for card in day_panel.select("div.res-card"):
                        cards.append((None, card))

                lesson_order = 0
                for stage_label, card in cards:
                    title = lesson_title(card)
                    inner_html = card.decode_contents().strip()
                    if stage_label:
                        display_title = f"{stage_label}: {title}" if stage_label != title else title
                    else:
                        display_title = title

                    base_slug = slugify(display_title)
                    slug = base_slug
                    n = 2
                    while slug in seen_lesson_slugs[module_slug]:
                        slug = f"{base_slug}-{n}"
                        n += 1
                    seen_lesson_slugs[module_slug].add(slug)

                    lesson_order += 1
                    module["lessons"].append({
                        "slug": slug,
                        "title": display_title,
                        "display_order": lesson_order,
                        "content_type": "html",
                        "content_body": inner_html,
                        "url": first_url(inner_html),
                        "est_minutes": None,
                    })

                if module["lessons"]:
                    modules.append(module)

    return {"lesson_css": lesson_css, "modules": modules}


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python scripts/import_iq_report.py <html-path> [out-path]", file=sys.stderr)
        sys.exit(2)
    html_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent.parent / "db" / "seed_modules.json"

    data = parse(html_path)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    by_vertical: dict[str, int] = {}
    lesson_total = 0
    for m in data["modules"]:
        by_vertical[m["vertical"]] = by_vertical.get(m["vertical"], 0) + 1
        lesson_total += len(m["lessons"])
    print(f"Wrote {out_path}")
    print(f"  {len(data['modules'])} modules, {lesson_total} lessons")
    for v, n in by_vertical.items():
        print(f"  {v}: {n} modules")


if __name__ == "__main__":
    main()
