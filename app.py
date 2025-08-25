import os
import json
import hashlib
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
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('extracted_images', filename)

@app.route('/dashboard-stats')
def get_dashboard_stats():
    """
    Returns statistics from the Elasticsearch index for the dashboard.
    """
    try:
        # Get total document count
        doc_count_response = es_client.count(index=INDEX_NAME)
        total_docs = doc_count_response['count']

        # Get folder aggregation data
        folder_aggs = es_client.search(
            index=INDEX_NAME,
            body={"aggs": {"top_folders": {"terms": {"field": "folder_name.keyword"}}}, "size": 0}
        )
        folder_buckets = folder_aggs['aggregations']['top_folders']['buckets']

        # Get file type aggregation data
        file_type_aggs = es_client.search(
            index=INDEX_NAME,
            body={"aggs": {"file_types": {"terms": {"script": "doc['metadata.filename.keyword'].value.substring(doc['metadata.filename.keyword'].value.lastIndexOf('.') + 1)"}}}, "size": 0}
        )
        file_type_buckets = file_type_aggs['aggregations']['file_types']['buckets']

        # Format data for the frontend
        folder_stats = [{'label': b['key'], 'value': b['doc_count']} for b in folder_buckets]
        file_type_stats = [{'label': b['key'].upper(), 'value': b['doc_count']} for b in file_type_buckets]

        return jsonify({
            'total_documents': total_docs,
            'folder_stats': folder_stats,
            'file_type_stats': file_type_stats
        })

    except Exception as e:
        print(f"An error occurred while fetching dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search():
    """
    Handles search queries and returns results.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify(results=[], stats=[])

    query_vector = model.encode(query).tolist()

    # The query no longer includes aggregations
    search_body = {
        "query": {
            "bool": {
                "should": [
                    {
                        "query_string": {
                            "query": query,
                            "fields": ["content", "figures.title"]
                        }
                    },
                    {
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
        "size": 100
    }

    try:
        response = es_client.search(index=INDEX_NAME, body=search_body)
        
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            filename = source.get('metadata', {}).get('filename', 'N/A')
            
            results.append({
                'filename': os.path.basename(filename),
                'content_snippet': source.get('content', '')[:250] + '...' if len(source.get('content', '')) > 250 else source.get('content', ''),
                'figures': source.get('figures', [])
            })

        # The 'stats' part of the response will now always be empty.
        # Your frontend should be updated to handle this, as the stats are now on the dashboard.
        return jsonify(results=results, stats=[])

    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)