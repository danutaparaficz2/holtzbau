import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# Configure Elasticsearch client
es_client = Elasticsearch("http://localhost:9200")
INDEX_NAME = "innocheque_documents"

# Load the same model used for indexing
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Initialize Flask application
app = Flask(__name__)

@app.route('/')
def index():
    """
    Renders the main search page.
    """
    return render_template('index.html')

# New route to serve image files
@app.route('/images/<path:filename>')
def serve_image(filename):
    """
    Serves image files from the extracted_images directory.
    """
    return send_from_directory('extracted_images', filename)

@app.route('/search')
def search():
    """
    Handles search queries, returns results, and folder statistics.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify(results=[], stats=[])

    # Generate an embedding for the user's query
    query_vector = model.encode(query).tolist()

    # Construct the hybrid search query
    search_body = {
        "query": {
            "bool": {
                "should": [
                    {  # Keyword search
                        "query_string": {
                            "query": query,
                            "fields": ["content", "figures.title"]
                        }
                    },
                    {  # Semantic search using knn
                        "script_score": {
                            "query": {
                                "match_all": {}
                            },
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                                "params": {
                                    "query_vector": query_vector
                                }
                            }
                        }
                    }
                ]
            }
        },
        "aggs": {
            "folders": {
                "terms": {
                    "field": "folder_name.keyword"
                }
            }
        },
        "size": 100
    }

    try:
        response = es_client.search(index=INDEX_NAME, body=search_body)
        
        # Extract and format the search results
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            filename = source.get('metadata', {}).get('filename', 'N/A')
            
            results.append({
                'filename': os.path.basename(filename),
                'content_snippet': source.get('content', '')[:250] + '...' if len(source.get('content', '')) > 250 else source.get('content', ''),
                'figures': source.get('figures', [])
            })

        # Extract and format the aggregation results
        stats = []
        if 'folders' in response['aggregations']:
            for bucket in response['aggregations']['folders']['buckets']:
                stats.append({
                    'folder': bucket['key'],
                    'doc_count': bucket['doc_count']
                })
            
        return jsonify(results=results, stats=stats)

    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)