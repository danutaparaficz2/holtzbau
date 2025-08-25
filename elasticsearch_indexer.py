import os
import json
import hashlib
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Configure Elasticsearch client
es_client = Elasticsearch("http://localhost:9200")
INDEX_NAME = "innocheque_documents"

# Define the index mapping with the new dense_vector field
MAPPING_BODY = {
    "properties": {
        "content": {"type": "text"},
        "metadata": {
            "properties": {
                "filename": {"type": "keyword"}
            }
        },
        "folder_name": {"type": "keyword"},
        "figures": {
            "type": "nested",
            "properties": {
                "title": {"type": "text"},
                "path": {"type": "keyword"}
            }
        },
        "content_vector": {
            "type": "dense_vector",
            "dims": 384,
            "index": True,
            "similarity": "cosine"
        }
    }
}

def generate_actions(data):
    """
    Generator function to format the data for bulk indexing.
    It reads from the new JSON format and correctly extracts all fields.
    """
    for doc in data:
        # Create a unique ID for the document based on its content
        doc_id = hashlib.sha256(doc.get('content', '').encode('utf-8')).hexdigest()

        # Extract all fields, handling potential missing keys
        filename = doc.get('metadata', {}).get('file_name', 'No Filename')
        folder_name = doc.get('folder_name', 'No Folder') 
        figures = doc.get('figures', [])
        content_vector = doc.get('content_vector', [])
        
        # Build the source dictionary to be indexed
        source_doc = {
            'content': doc.get('content', ''),
            'metadata': {
                'filename': filename,
            },
            'folder_name': folder_name,
            'figures': figures,
            'content_vector': content_vector
        }
        
        yield {
            "_index": INDEX_NAME,
            "_id": doc_id,
            "_source": source_doc,
        }

def main():
    """
    The main function to orchestrate the indexing process.
    """
    # The path to the JSON file created by data_preprocessing.py
    json_file_path = 'prepared_data.json'
    
    if not os.path.exists(json_file_path):
        print(f"Error: The file '{json_file_path}' does not exist.")
        print("Please run `python data_preprocessing.py` first to create the data file.")
        return

    # Create the index with the custom mapping before indexing
    if es_client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists. To re-index, please delete it first.")
        print(f"Run: curl -X DELETE \"localhost:9200/{INDEX_NAME}\"")
        return
    else:
        print(f"Creating index '{INDEX_NAME}' with custom mapping...")
        es_client.indices.create(index=INDEX_NAME, body={"mappings": MAPPING_BODY})
        print("Index created.")

    # Load the data from the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    if not documents:
        print("The JSON file is empty. No documents to index.")
        return
        
    print(f"Found {len(documents)} documents. Indexing documents...")

    try:
        # Index documents in bulk
        success, failed = bulk(es_client, generate_actions(documents))
        print(f"Indexed {success} documents successfully.")
    except Exception as e:
        print(f"An error occurred during bulk indexing: {e}")

if __name__ == "__main__":
    main()