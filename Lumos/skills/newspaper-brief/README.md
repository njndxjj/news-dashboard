# Newspaper Brief Skill

## Description
This skill renders RSS news data into "newspaper-style" long images.

## Usage
1. Prepare JSON-format news data.
2. Run the `render_newspaper.py` script to transform data into PNG image.

## Example Commands:
### Step 1: Fetch RSS News
```bash
python fetch_rss.py
```

### Step 2: Render Newspaper
```bash
python render_newspaper.py
```

---

## Dependencies
- Python 3
- Libraries: `Pillow`, `feedparser`
- Fonts: Arial (or default provided by system)

---

## Outputs
- News JSON file: `output/rss_news.json`
- Newspaper image: `output/newspaper.png`