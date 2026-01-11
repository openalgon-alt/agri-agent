import json
import os
import time
import shutil
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None # Handle gracefully if not installed

from langchain_core.documents import Document
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

class RAGEngine:
    def __init__(self, pdf_folder="./pdfs", db_dir="./chroma_db_pro"):
        self.pdf_folder = pdf_folder
        self.db_dir = db_dir
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=self.ollama_url)
        self.vector_db = None

    def initialize_db(self, progress_callback=None):
        """Initializes the Vector DB. Loads if exists, creators if empty."""
        if not os.path.exists(self.pdf_folder):
            os.makedirs(self.pdf_folder)
            
        # Check if DB exists and has data
        if os.path.exists(self.db_dir) and os.listdir(self.db_dir):
            self.vector_db = Chroma(persist_directory=self.db_dir, embedding_function=self.embeddings)
            return self.vector_db, [] # No new chunks

        # Otherwise, load from PDFs
        return self._rebuild_index(progress_callback)

    def _rebuild_index(self, progress_callback=None):
        if progress_callback: progress_callback(10, "Scanning PDFs...")
        
        if not os.path.exists(self.pdf_folder) or not os.listdir(self.pdf_folder):
            return None, []

        docs = []
        if DOCLING_AVAILABLE:
            if progress_callback: progress_callback(20, "Using Docling for High-Quality Extraction (This is slower but better)...")
            converter = DocumentConverter()
            pdf_files = [f for f in os.listdir(self.pdf_folder) if f.lower().endswith('.pdf')]
            
            for i, file_name in enumerate(pdf_files):
                if progress_callback: 
                   progress = 20 + int((i / len(pdf_files)) * 20) # 20% to 40%
                   progress_callback(progress, f"Analyzing layout: {file_name}")
                
                file_path = os.path.join(self.pdf_folder, file_name)
                try:
                    # Convert PDF to Markdown
                    result = converter.convert(file_path)
                    markdown_text = result.document.export_to_markdown()
                    
                    # Create LangChain Document
                    # We treat the whole file as one doc first, then split it.
                    doc = Document(
                        page_content=markdown_text,
                        metadata={"source": file_name}
                    )
                    docs.append(doc)
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
        else:
            if progress_callback: progress_callback(20, "Docling not found. Fallback to Standard Loader...")
            loader = DirectoryLoader(self.pdf_folder, glob="./*.pdf", loader_cls=PyPDFLoader)
            docs = loader.load()
        
        if progress_callback: progress_callback(40, "Splitting Text...")
        
        # Use a larger chunk size for Markdown to keep sections together
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
        chunks = text_splitter.split_documents(docs)
        
        if progress_callback: progress_callback(50, f"Embedding {len(chunks)} chunks...")
        
        self.vector_db = Chroma.from_documents(
            documents=chunks, 
            embedding=self.embeddings, 
            persist_directory=self.db_dir
        )
        
        if progress_callback: progress_callback(100, "Indexing Complete!")
        return self.vector_db, chunks

    def get_qa_chain(self, model_type="local", api_key=None, catalog_context="", local_model="llama3.2"):
        if not self.vector_db:
            return None

        # 1. Select LLM
        if model_type == "cloud":
            if not ChatGoogleGenerativeAI:
                return "ERROR: `langchain-google-genai` not installed."
            if not api_key:
                return "ERROR: Google API Key required for Cloud model."
            
            llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key, temperature=0.3)
        else:
            # Switch between local models
            llm = ChatOllama(model=local_model, temperature=0, base_url=self.ollama_url)

        # 2. Optimized Prompt
        # We inject the catalog directly into the system instructions if provided.
        catalog_section = ""
        if catalog_context:
            catalog_section = f"""
            MASTER CATALOG OF ALL ARTICLES (Use this for 'list all' or 'who wrote' questions):
            {catalog_context}
            """

        template = f"""You are a Virtual Agronomist. Use the following context to answer the question.
        
        {catalog_section}
        
        RETRIEVED CONTEXT (Specific Excerpts):
        {{context}}
        
        Rules:
        1. Only answer based on the context above (Master Catalog + Retrieved Context).
        2. If asking for a list of articles/authors, USE THE MASTER CATALOG.
        3. If the context mentions specific dates (like 2025), prioritize that information.
        
        Question: {{question}}
        Answer:"""
        
        QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

        # Search parameters k=3 for more context
        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        return qa_chain

    def search(self, query: str, k=1):
        """Direct search for tools."""
        if not self.vector_db:
            return []
        return self.vector_db.similarity_search(query, k=k)

    def extract_metadata_from_text(self, text: str):
        """Uses LLM to extract title and authors from text."""
        try:
            llm = ChatOllama(model="llama3.2", temperature=0, format="json", base_url=self.ollama_url)
            prompt = f"""Extract the 'title' and 'authors' (list of strings) from the following text. 
            Return ONLY valid JSON.
            
            TEXT:
            {text[:2000]}
            """
            response = llm.invoke(prompt)
            data = json.loads(response.content)
            return data.get("title", "Unknown Title"), data.get("authors", ["Unknown"])
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return "Unknown Title", ["Unknown"]

    def sync_new_files(self, metadata_path="./metadata.json"):
        """Checks for PDFs not in metadata.json and indexes them incrementally. Yields status updates."""
        
        yield json.dumps({"status": "Checking metadata...", "percent": 0})
        # 1. Load Metadata
        existing_filenames = set()
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                try:
                    meta_list = json.load(f)
                    for item in meta_list:
                        existing_filenames.add(item.get("filename"))
                except:
                    pass 

        # 2. Identify New Files
        if not os.path.exists(self.pdf_folder):
             yield json.dumps({"status": "Error: PDF Folder missing.", "percent": 0})
             return
        

        all_pdfs = [f for f in os.listdir(self.pdf_folder) if f.split('.')[-1].lower() == 'pdf']
        
        new_files = [f for f in all_pdfs if f not in existing_filenames]
        
        if not new_files:
            yield json.dumps({"status": "No new files to sync.", "percent": 100})
            return

        yield json.dumps({"status": f"Found {len(new_files)} new files.", "percent": 5})

        # 3. Process New Files
        docs = []
        new_metadata_entries = []
        
        if not self.vector_db:
             yield json.dumps({"status": "Initializing Database...", "percent": 5})
             self.initialize_db()

        if not DOCLING_AVAILABLE:
             yield json.dumps({"status": "Error: Docling not available. Please install it.", "percent": 0})
             return

        converter = DocumentConverter()
        total_files = len(new_files)
        
        for i, file_name in enumerate(new_files):
            percent = 10 + int((i / total_files) * 40) # 10% to 50%
            yield json.dumps({"status": f"Processing {file_name}...", "percent": percent})
            
            file_path = os.path.join(self.pdf_folder, file_name)
            try:
                # Convert
                result = converter.convert(file_path)
                markdown_text = result.document.export_to_markdown()
                
                # Extract Metadata
                yield json.dumps({"status": f"Extracting metadata for {file_name}...", "percent": percent})
                title, authors = self.extract_metadata_from_text(markdown_text)
                
                new_metadata_entries.append({
                    "filename": file_name,
                    "title": title,
                    "authors": authors
                })
                
                docs.append(Document(page_content=markdown_text, metadata={"source": file_name}))
                
            except Exception as e:
                print(f"Error {file_name}: {e}")
                
        if not docs:
            yield json.dumps({"status": "Failed to extract text from files.", "percent": 0})
            return

        # 4. Split and Add
        yield json.dumps({"status": "Splitting text...", "percent": 55})
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
        chunks = text_splitter.split_documents(docs)
        
        yield json.dumps({"status": f"Embedding {len(chunks)} chunks...", "percent": 60})
        
        if self.vector_db:
            self.vector_db.add_documents(chunks)
        else:
             self.vector_db = Chroma.from_documents(chunks, self.embeddings, persist_directory=self.db_dir)

        # 5. Update Metadata
        yield json.dumps({"status": "Saving metadata...", "percent": 95})
        
        final_list = []
        if os.path.exists(metadata_path):
             with open(metadata_path, 'r', encoding='utf-8') as f:
                 try: final_list = json.load(f)
                 except: pass
        
        final_list.extend(new_metadata_entries)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, indent=4)
            
        yield json.dumps({"status": f"Successfully synced {len(new_files)} files!", "percent": 100})
