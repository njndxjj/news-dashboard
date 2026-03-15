import sqlite3
import matplotlib.pyplot as plt


def generate_report():
    """Generate a visual report from the SQLite database."""
    conn = sqlite3.connect("../processor/output/news_analysis.db")
    c = conn.cursor()
    categories = {}

    # Fetch data from database
    for row in c.execute("SELECT category, COUNT(*) FROM analysis GROUP BY category"):
        categories[row[0]] = row[1]

    conn.close()

    # Create Pie Chart
    labels = categories.keys()
    sizes = categories.values()
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("News Category Distribution")
    plt.savefig("output/report.png")
    plt.show()

    print("Report generated successfully.")

if __name__ == "__main__":
    generate_report()