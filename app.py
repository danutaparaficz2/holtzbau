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

# Function to get file extension in a safe way
def get_file_extension(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].upper()
    return 'UNKNOWN'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('extracted_images', filename)

@app.route('/dashboard-stats')
def get_dashboard_stats():
    """
    Returns statistics from the Elasticsearch index.
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

        # Get all documents and process them in Python to get file types
        all_docs_search = es_client.search(
            index=INDEX_NAME,
            body={"query": {"match_all": {}}, "_source": ["metadata.filename"], "size": 10000}
        )
        
        file_type_counts = {}
        for hit in all_docs_search['hits']['hits']:
            filename = hit['_source']['metadata']['filename']
            file_type = get_file_extension(filename)
            file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
        
        # Format data for the frontend
        folder_stats = [{'label': b['key'], 'value': b['doc_count']} for b in folder_buckets]
        file_type_stats = [{'label': key, 'value': value} for key, value in file_type_counts.items()]

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

        return jsonify(results=results, stats=[])

    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)