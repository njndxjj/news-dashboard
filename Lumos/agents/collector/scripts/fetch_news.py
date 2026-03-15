import requests
from bs4 import BeautifulSoup
import json

def fetch_news():
    """Fetch news from a predefined source."""
    url = "https://example-news-site.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        for item in soup.find_all("div", class_="news-item"):
            title = item.find("h2").get_text(strip=True)
            summary = item.find("p").get_text(strip=True) if item.find("p") else ""
            link = item.find("a")["href"]
            articles.append({"title": title, "summary": summary, "link": link})

        # Output to JSON
        with open("output/news.json", "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        print("News fetched and saved successfully.")
    else:
        print(f"Failed to fetch news: HTTP {response.status_code}")

if __name__ == "__main__":
    fetch_news()