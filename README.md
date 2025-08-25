#Holzbau Document Search
## Project Overview
This project is a sophisticated document search engine designed to demonstrate a proof of concept for a company's internal knowledge base. It allows users to search for documents based on keywords and provides rich results, including text snippets, folder statistics, and extracted figures with their titles and images. The project utilizes a full-stack approach with Python, Elasticsearch, and Flask.

The entire system is based on a data-driven funnel, transforming raw files into a structured, searchable knowledge base.

## Key Features
### Full-Text Search: Search for keywords across document content.

### Figure Search: Find relevant figures by searching for keywords in their titles.

### Dynamic Image Display: View extracted figures directly in the search results, with a toggle button to keep the UI clean.

### Folder Statistics: Get a breakdown of which folders contain the most relevant documents.

### Scalable Backend: Uses Elasticsearch for efficient and powerful indexing and querying.

### User-Friendly Interface: A simple web application built with Flask and HTML/CSS/JS.

## Setup and Installation
Prerequisites
Python 3.x

Elasticsearch (version 8.x is recommended)

Required Python libraries: flask, elasticsearch, pymupdf, python-docx, pillow

Step-by-Step Guide
Clone the Repository
Start by cloning or downloading the project files.

Install Python Libraries
Navigate to your project directory and install the necessary dependencies:

Bash

pip install Flask elasticsearch PyMuPDF python-docx Pillow
Install and Run Elasticsearch
Ensure you have an Elasticsearch instance running on http://localhost:9200. You can use Docker for a quick setup.

Bash

docker pull docker.elastic.co/elasticsearch/elasticsearch:8.14.0
docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.14.0
Process and Index Your Data
First, configure the data_directory variable in data_preprocessing.py to point to the folder containing your documents. Then, run the data pipeline scripts in order:

## Data Preprocessing: This script extracts text and images from your documents and saves them to a prepared_data.json file. It also creates a new extracted_images folder.

Bash

python data_preprocessing.py
Index Creation: This script connects to Elasticsearch, deletes any old index, and loads your prepared data.

Bash

# Optional: Delete old index if it exists
curl -X DELETE "localhost:9200/innocheque_documents"

# Index the new data
python elasticsearch_indexer.py
Run the Web Application
Start the Flask web server. The application will be accessible at http://localhost:5000.

Bash

python app.py
📂 Project Structure
holzbau-search/
├── app.py                     # The main Flask application
├── data_preprocessing.py      # Script for data extraction and cleaning
├── elasticsearch_indexer.py   # Script for indexing data into Elasticsearch
├── index.html                 # The frontend web page
├── prepared_data.json         # (Generated) JSON file with extracted data
├── extracted_images/          # (Generated) Folder for extracted figures
└── README.md                  # This file
