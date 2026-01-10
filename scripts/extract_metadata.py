import os
import json
import logging
from tqdm import tqdm
from docling.document_converter import DocumentConverter
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Configure logging to suppress noisy libraries
logging.getLogger("docling").setLevel(logging.ERROR)
logging.getLogger("pypdf").setLevel(logging.ERROR)

PDF_DIR = "./pdfs"
OUTPUT_FILE = "metadata.json"

def extract_metadata():
    if not os.path.exists(PDF_DIR):
        print("PDF directory not found.")
        return

    # Initialize Docling (Structure) and LLM (Intelligence)
    print("Initializing Docling Converter...")
    converter = DocumentConverter()
    
    print("Initializing Ollama (llama3.2)...")
    llm = ChatOllama(model="llama3.2", temperature=0, format="json")
    
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template="""You are a librarian. Extract the 'title' and 'authors' from the following ACADEMIC PAPER HEADER (Markdown format).
        
        Rules:
        1. Title: Clean up spacing. Remove "Volume 01", "ISSN" etc.
        2. Authors: Extract ONLY the names. Exclude universities, emails, "Corresponding Author", "Department of...", etc.
        3. Return JSON: {{ "title": "String", "authors": ["Name 1", "Name 2"] }}
        
        Document Header (Markdown):
        {text}
        """,
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    metadata_index = []
    
    print(f"Extracting High-Quality Metadata from {len(pdf_files)} files...")
    print("Note: This uses Docling + LLM, so it will take ~10-20 seconds per file.")
    
    for filename in tqdm(pdf_files):
        path = os.path.join(PDF_DIR, filename)
        entry = {
            "filename": filename,
            "title": filename,
            "authors": []
        }
        
        try:
            # 1. Use Docling to get clean Markdown (preserves layout, separates headers)
            # We capture the first 1000 characters of Markdown which usually contains the header
            result = converter.convert(path)
            full_md = result.document.export_to_markdown()
            
            # Heuristic: The Title/Author is almost always in the first 40 lines of markdown
            header_md = "\n".join(full_md.split("\n")[:40])
            
            # 2. Feed Clean Markdown to LLM
            res = chain.invoke({"text": header_md})
            
            entry["title"] = res.get("title", filename)
            entry["authors"] = res.get("authors", [])
            
            # Fallback if LLM returns empty
            if not entry["title"]: entry["title"] = filename
            
        except Exception as e:
            # print(f"Error on {filename}: {e}") # Keep UI clean
            pass
            
        metadata_index.append(entry)
        
        # Save incrementally in case of crash
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata_index, f, indent=4)

    print(f"\nSuccess! Metadata saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_metadata()
