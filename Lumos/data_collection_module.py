import requests
from bs4 import BeautifulSoup
import json

def scrape_website(url):
    """Scrape the content of a webpage."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    else:
        print(f"Failed to fetch {url}: Status code {response.status_code}")
        return None

def parse_news(soup):
    """Parse the news content from the soup object."""
    news_items = []
    for item in soup.find_all('div', class_='news-item'):  # Update with actual CSS class
        title = item.find('h2').get_text(strip=True)
        link = item.find('a')['href']
        summary = item.find('p').get_text(strip=True) if item.find('p') else ""
        news_items.append({
            'title': title,
            'link': link,
            'summary': summary
        })
    return news_items

def fetch_social_media(api_url, headers, params):
    """Fetch data from a social media API endpoint."""
    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch API data: Status code {response.status_code}")
        return None

if __name__ == "__main__":
    # Example for web scraping
    example_url = "https://example-news-site.com"
    soup = scrape_website(example_url)
    if soup:
        news = parse_news(soup)
        with open('news_output.json', 'w') as f:
            json.dump(news, f, ensure_ascii=False, indent=2)

    # Example for social media API
    example_api_url = "https://api.example.com/v1/posts"
    example_headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
    }
    example_params = {
        'q': '热点',
        'lang': 'zh'
    }
    social_data = fetch_social_media(example_api_url, example_headers, example_params)
    if social_data:
        with open('social_output.json', 'w') as f:
            json.dump(social_data, f, ensure_ascii=False, indent=2)