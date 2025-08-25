import os
import json
import re
import fitz  # PyMuPDF library for PDF processing
from PIL import Image
from docx import Document

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    """
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
    return text

def extract_text_from_docx(docx_path):
    """
    Extracts text from a DOCX file.
    """
    text = ""
    try:
        doc = Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX {docx_path}: {e}")
    return text

def find_figure_titles(text):
    """
    Finds and extracts figure titles from text using a regular expression.
    """
    figure_titles = []
    # This regex looks for "Figure" followed by a number or letter, a colon, and then the title.
    pattern = re.compile(r'(Figure\s+\S+:)(.+)', re.IGNORECASE)
    for line in text.split('\n'):
        match = pattern.search(line)
        if match:
            figure_titles.append(match.group().strip())
    return figure_titles

def extract_images_from_pdf(pdf_path, output_dir="extracted_images"):
    """
    Extracts images from a PDF and saves them as PNG files.
    Returns a list of paths to the saved images.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_paths = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num] # Get a Page object
            
            # Now call get_images() on the Page object
            for i, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Create a unique filename for the image
                pdf_filename_base = os.path.splitext(os.path.basename(pdf_path))[0]
                image_name = f"{pdf_filename_base}_page{page_num}_{i}.{image_ext}"
                image_path = os.path.join(output_dir, image_name)

                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                if image_ext != "png":
                    try:
                        img_pil = Image.open(image_path)
                        png_path = image_path.replace(f".{image_ext}", ".png")
                        img_pil.save(png_path)
                        os.remove(image_path)
                        image_path = png_path
                    except Exception as e:
                        print(f"Failed to convert image {image_name}: {e}")
                        continue

                image_paths.append(image_path)
        doc.close()

    except Exception as e:
        print(f"Error extracting images from PDF {pdf_path}: {e}")
    
    return image_paths

def extract_content_from_file(file_path):
    """
    Identifies the file type and extracts its content and images.
    """
    if file_path.lower().endswith('.pdf'):
        image_paths = extract_images_from_pdf(file_path)
        text = extract_text_from_pdf(file_path)
        return text, image_paths
    elif file_path.lower().endswith('.docx'):
        print(f"Skipping image extraction for DOCX file: {file_path}")
        return extract_text_from_docx(file_path), []
    elif file_path.lower().endswith(('.jpg', '.png', '.jpeg', '.dwg', '.dxf')):
        print(f"Skipping unsupported file type for text/image extraction: {file_path}")
        return "", []
    else:
        print(f"Skipping unsupported file type: {file_path}")
        return "", []

def prepare_data_for_indexing(directory_path, output_file='prepared_data.json'):
    """
    Walks through a directory, extracts content from supported files, and saves it to a JSON file.
    """
    data_list = []
    
    for root, dirs, files in os.walk(directory_path):
        folder_name = os.path.relpath(root, directory_path)
        if folder_name == '.':
            folder_name = 'root'

        for file in files:
            file_path = os.path.join(root, file)
            print(f"Processing file: {file_path}")
            
            content, image_paths = extract_content_from_file(file_path)

            if content:
                figure_titles = find_figure_titles(content)
                
                figures = []
                for i, title in enumerate(figure_titles):
                    img_path = image_paths[i] if i < len(image_paths) else None
                    if img_path:
                        figures.append({"title": title, "path": img_path})

                document = {
                    "content": content,
                    "metadata": {
                        "file_name": file,
                        "file_path": file_path
                    },
                    "folder_name": folder_name,
                    "figures": figures 
                }
                data_list.append(document)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    
    print(f"\nSuccessfully prepared {len(data_list)} documents.")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    data_directory = '/Users/danuta.paraficz/Documents/Projects'
    
    if not os.path.isdir(data_directory):
        print(f"Error: The directory '{data_directory}' does not exist.")
        print("Please update the 'data_directory' variable to the correct path.")
    else:
        prepare_data_for_indexing(data_directory)