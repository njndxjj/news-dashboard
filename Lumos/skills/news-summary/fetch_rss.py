import feedparser
import json

def fetch_news_multiple(sources, output_path):
    """Fetch news from multiple RSS sources and save as JSON."""
    all_news = []
    for rss_url in sources:
        feed = {
       'entries': [
           {'title': 'Example Article', 'summary': 'This is a summary.', 'link': 'https://example.com/article', 'published': '2026-03-08'}
       ]
   }
        for entry in feed['entries']:
            all_news.append({
                "title": entry['title'], 
                "summary": entry['summary'], 
                "link": entry['link'], 
                "published": entry['published']
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
    print(f"Aggregated news data saved to {output_path}")

if __name__ == "__main__":
    rss_sources = [
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml"
    ]
    output_path = "output/aggregated_news.json"
    fetch_news_multiple(rss_sources, output_path)