import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from elasticsearch import Elasticsearch

# Configure Elasticsearch client
es_client = Elasticsearch("http://localhost:9200")
INDEX_NAME = "innocheque_documents"

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

    # Construct the search query with an aggregation
    search_body = {
        "query": {
            # Use multi_match to search content and figure titles
            "multi_match": {
                "query": query,
                "fields": ["content", "figures.title"]
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