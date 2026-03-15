import requests
from bs4 import BeautifulSoup
import feedparser

def scrape_portal(url):
    """Scrape a news portal for articles."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        for item in soup.select('.article-item'):  # Replace with actual class
            title = item.select_one('.title').get_text(strip=True)
            link = item.select_one('a')['href']
            summary = item.select_one('.summary').get_text(strip=True)
            articles.append({'title': title, 'link': link, 'summary': summary})
        return articles
    else:
        return []

def parse_rss_feed(url):
    """Parse RSS feed for articles."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary if 'summary' in entry else ""
        })
    return articles

if __name__ == "__main__":
    # Example usage
    portal_url = "https://example.com/news"
    rss_url = "https://example.com/rss"
    print("Portal Articles:", scrape_portal(portal_url))
    print("RSS Articles:", parse_rss_feed(rss_url))