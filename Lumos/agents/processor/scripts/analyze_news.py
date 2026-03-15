import sqlite3
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def analyze_and_store():
    """Analyze news and store results in SQLite DB."""
    # Load news data
    with open("output/aggregated_news.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Classify articles
    categories = {
        "Technology": ["AI", "machine learning", "innovation"],
        "Finance": ["stock market", "growth", "investment"],
    }
    vectorizer = CountVectorizer()

    conn = sqlite3.connect("output/news_analysis.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS analysis (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     title TEXT,
                     summary TEXT,
                     link TEXT,
                     category TEXT)''')

    for article in articles:
        best_category = "Uncategorized"
        max_similarity = 0
        for category, keywords in categories.items():
            docs = [' '.join(keywords), article['summary']]
            matrix = vectorizer.fit_transform(docs)
            similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            if similarity > max_similarity:
                max_similarity = similarity
                best_category = category

        # Store in database
        c.execute('''INSERT INTO analysis (title, summary, link, category) VALUES (?, ?, ?, ?)''',
                  (article['title'], article['summary'], article['link'], best_category))

    conn.commit()
    conn.close()
    print("Analysis completed and data stored.")

if __name__ == "__main__":
    analyze_and_store()