from neo4j import GraphDatabase

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_article_node(self, title, summary, link, category):
        """Create a node for an article in the graph."""
        query = (
            "CREATE (a:Article {title: $title, summary: $summary, link: $link, category: $category})"
        )
        with self.driver.session() as session:
            session.run(query, title=title, summary=summary, link=link, category=category)

    def create_relationship(self, title_1, title_2, relation):
        """Create a relationship between two articles."""
        query = (
            "MATCH (a1:Article {title: $title_1}), (a2:Article {title: $title_2}) "
            "CREATE (a1)-[:RELATION {type: $relation}]->(a2)"
        )
        with self.driver.session() as session:
            session.run(query, title_1=title_1, title_2=title_2, relation=relation)

if __name__ == "__main__":
    # Example connection (replace with actual credentials)
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"

    kg = KnowledgeGraph(uri, user, password)

    # Example articles
    kg.create_article_node("Tech news", "New AI techniques are transforming industries.", "https://example.com/tech", "Technology")
    kg.create_article_node("Market updates", "Stock market sees unprecedented growth.", "https://example.com/market", "Finance")

    # Example relationship
    kg.create_relationship("Tech news", "Market updates", "related")

    kg.close()