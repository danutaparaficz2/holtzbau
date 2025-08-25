
# Holzbau Document Search

## 📄 Project Overview

This project is a sophisticated document search engine designed to demonstrate a proof of concept for a company's internal knowledge base. It allows users to search for documents using hybrid search, which combines keyword matching with AI-powered semantic understanding. The system provides rich results, including text snippets, folder statistics, and extracted figures with their titles and images. The project utilizes a full-stack approach with Python, Elasticsearch, and Flask.

The entire system is based on a data-driven funnel, transforming raw files into a structured, searchable knowledge base.
<img width="1981" height="2088" alt="_- visual selection" src="https://github.com/user-attachments/assets/d1f56ca2-3c38-4248-9214-6609c29ec2ae" />


Given a 200 GB PDF dataset, the time it would take to prepare and index the data on your Mac is difficult to estimate precisely, but we can make an informed projection. The total time depends heavily on three main factors: **disk I/O speed**, **CPU processing power**, and **network bandwidth** to Elasticsearch.

---

### Key Factors Affecting the Timeline

* **PDF Processing:** Extracting text and especially images from PDFs is **the most time-consuming part** of the process. On a modern Mac (M1/M2/M3 chip with an SSD), a single multi-page PDF might take anywhere from a few seconds to a few minutes, depending on its complexity (e.g., number of images, quality of text). The average processing speed could be around **1-5 MB/s**. At this rate, processing 200 GB of data would take approximately **11 to 55 hours**.
* **Indexing:** The bulk indexing process is much faster. Once the data is in the JSON format, Elasticsearch can ingest it very quickly. On a local network, you can expect an indexing speed of **10-50 MB/s**. This part of the process would likely take **1 to 6 hours**.
* **Overhead:** This includes Python script startup time, file system traversal, and small latencies. While generally a minor factor, it can add up over a large dataset.

---

### Estimated Time Breakdown

| Process | Estimated Speed | Time Calculation | Projected Time |
| :--- | :--- | :--- | :--- |
| **Data Processing** | 1-5 MB/s | (200,000 MB) / (1-5 MB/s) | **~11 to 55 hours** |
| **Indexing** | 10-50 MB/s | (200,000 MB) / (10-50 MB/s) | **~1 to 6 hours** |
| **Total Estimated Time** | | | **~12 to 61 hours** |

In a realistic scenario, with a typical mix of simple and complex PDF files, you should expect the entire process to take **at least 2 days** of continuous operation. The most significant bottleneck will be the `data_preprocessing.py` script due to the intensive I/O and CPU operations involved in parsing and extracting data from each individual file.

-----

## 🚀 Key Features

  * **Hybrid Search:** Combines traditional keyword search with a semantic search model (paraphrase-multilingual-MiniLM-L12-v2) for more accurate and relevant results.
  * **Full-Text Search:** Search for keywords across document content.
  * **Figure Search:** Find relevant figures by searching for keywords in their titles.
  * **Dynamic Image Display:** View extracted figures directly in the search results, with a toggle button to keep the UI clean.
  * **Folder Statistics:** Get a breakdown of which folders contain the most relevant documents.
  * **Scalable Backend:** Uses Elasticsearch for efficient and powerful indexing and querying.
  * **User-Friendly Interface:** A simple web application built with Flask and HTML/CSS/JS.

-----

## 🛠️ Setup and Installation

### Prerequisites

  * Python 3.x
  * Elasticsearch (version 8.x is recommended)
  * Required Python libraries: `flask`, `elasticsearch`, `pymupdf`, `python-docx`, `pillow`, `sentence-transformers`

### Step-by-Step Guide

1.  **Clone the Repository**
    Start by cloning or downloading the project files.

2.  **Install Python Libraries**
    Navigate to your project directory and install the necessary dependencies:

    ```bash
    pip install Flask elasticsearch PyMuPDF python-docx Pillow sentence-transformers
    ```

3.  **Install and Run Elasticsearch**
    Ensure you have an Elasticsearch instance running on `http://localhost:9200`. You can use Docker for a quick setup.

    ```bash
    docker pull docker.elastic.co/elasticsearch/elasticsearch:8.14.0
    docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.14.0
    ```

4.  **Process and Index Your Data**
    First, configure the `data_directory` variable in `data_preprocessing.py` to point to the folder containing your documents. Then, run the data pipeline scripts in order:

      * **Data Preprocessing:** This script extracts text and images from your documents and saves them to a `prepared_data.json` file. It also creates a new `extracted_images` folder.
        ```bash
        python data_preprocessing.py
        ```
      * **Index Creation:** This script connects to Elasticsearch, deletes any old index, and loads your prepared data.
        ```bash
        # Optional: Delete old index if it exists
        curl -X DELETE "localhost:9200/innocheque_documents"

        # Index the new data
        python elasticsearch_indexer.py
        ```

5.  **Run the Web Application**
    Start the Flask web server. The application will be accessible at `http://localhost:5000`.

    ```bash
    python app.py
    ```

-----

## 📂 Project Structure

```
holzbau-search/
├── app.py                     # The main Flask application
├── data_preprocessing.py      # Script for data extraction and cleaning
├── elasticsearch_indexer.py   # Script for indexing data into Elasticsearch
├── index.html                 # The frontend web page
├── prepared_data.json         # (Generated) JSON file with extracted data
├── extracted_images/          # (Generated) Folder for extracted figures
└── README.md                  # This file
```

