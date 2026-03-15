import sqlite3
from typing import List, Dict
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Database setup
def init_db(db_name="hotspot_data.db"):
    """Initialize SQLite database."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    summary TEXT,
                    link TEXT,
                    category TEXT)''')
    conn.commit()
    conn.close()

# Data classification
def classify_articles(articles: List[Dict], categories: Dict[str, List[str]]) -> List[Dict]:
    """Classify articles into predefined categories based on keywords."""
    classified = []
    vectorizer = CountVectorizer()
    for article in articles:
        best_category = "Uncategorized"
        max_similarity = 0
        for category, keywords in categories.items():
            # Compute similarity with category keywords
            docs = [' '.join(keywords), article['summary']]
            matrix = vectorizer.fit_transform(docs)
            similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            if similarity > max_similarity:
                max_similarity = similarity
                best_category = category
        article['category'] = best_category
        classified.append(article)
    return classified

if __name__ == "__main__":
    # Example usage
    init_db()

    # Simulated articles
    articles = [
        {"title": "Tech news", "summary": "New AI techniques are transforming industries.", "link": "https://example.com/tech1"},
        {"title": "Market updates", "summary": "Stock market sees unprecedented growth in Q4.", "link": "https://example.com/market"},
    ]

    # Example categories
    categories = {
        "Technology": ["AI", "machine learning", "technology", "innovation"],
        "Finance": ["stock market", "quarter", "growth", "finance"],
    }

    classified_articles = classify_articles(articles, categories)

    # Store classified articles into database
    conn = sqlite3.connect("hotspot_data.db")
    c = conn.cursor()
    for article in classified_articles:
        c.execute('''INSERT INTO articles (title, summary, link, category) VALUES (?, ?, ?, ?)''',
                  (article['title'], article['summary'], article['link'], article['category']))
    conn.commit()
    conn.close()
    print("Articles processed and stored in database.")