from flask import Flask, jsonify
from knowledge_graph import KnowledgeGraph

app = Flask(__name__)

@app.route('/api/graph', methods=['GET'])
def graph_data():
    try:
        kg = KnowledgeGraph("bolt://localhost:7687", "neo4j", "password")
        query = "MATCH (a:Article) RETURN a.title, a.summary, a.link, a.category LIMIT 10"
        result = []
        
        with kg.driver.session() as session:
            for record in session.run(query):
                result.append({
                    "title": record["a.title"],
                    "summary": record["a.summary"],
                    "link": record["a.link"],
                    "category": record["a.category"]
                })
        
        kg.close()
        return jsonify({"data": result}), 200
    except Exception as e:
        print(f"Error fetching graph data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)