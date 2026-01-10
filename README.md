# Virtual Agronomist - AI Knowledge Base

Welcome to **AgriCatalogues Pro AI**, an advanced RAG (Retrieval-Augmented Generation) application designed to serve as a Virtual Agronomist. This system ingests agricultural magazines (PDFs), extracts high-quality metadata, and allows users to query the knowledge base using local or cloud-based AI.

## 🌟 Key Features

*   **Modular RAG Engine**: Logic separated from UI for maintainability (`rag_engine.py` + `app.py`).
*   **Dual AI Models**:
    *   **Local**: Runs 100% offline using **Ollama** (Llama 3.2 3B).
    *   **Cloud**: Uses **Google Gemini Pro** for enhanced reasoning.
*   **AMD GPU Acceleration**: Fully optimized for AMD RX 6600 using Vulkan back-end on Windows.
*   **High-Quality Metadata**: Combines **Docling** (Layout parsing) and **LLM** (extraction) to accurately identify Titles and Authors from PDFs.
*   **Global Knowledge Injection**: Injects the full catalog of articles into the AI's context, enabling perfect "List all articles" answers.
*   **Admin Dashboard**: Upload new PDFs and re-index the database directly from the UI.

## 📂 Project Structure

*   `app.py`: Main Streamlit application entry point.
*   `rag_engine.py`: Core logic for Vector DB (Chroma), Embeddings, and LLM chains.
*   `admin_dashboard.py`: UI component for file management and stats.
*   `metadata.json`: Auto-generated database of document titles and authors.
*   `start_app.bat`: One-click launcher (sets up environment variables automatically).
*   `pdfs/`: Directory storing the raw magazine files.
*   `chroma_db_pro/`: Persisted Vector Database.
*   `scripts/`: Utility scripts for debugging and metadata generation.
    *   `extract_metadata.py`: Standalone script to regenerate `metadata.json`.
    *   `debug_gpu.bat`: Tool to verification GPU usage.

## 🚀 Installation & Setup

1.  **Prerequisites**:
    *   Python 3.10+
    *   [Ollama](https://ollama.com/) installed and running.
    *   AMD GPU Drivers (if using AMD).

2.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    Simply double-click **`start_app.bat`**.
    *   This script automatically sets `OLLAMA_VULKAN=1` for AMD GPU support.
    *   It activates the virtual environment and launches Streamlit.

## 💡 How it Works

1.  **Ingestion**: When you upload a PDF, the system converts it to text.
    *   *Note*: For best results, ensuring `metadata.json` is up to date is crucial. You can run `python scripts/extract_metadata.py` if needed.
2.  **Indexing**: The text is chunked and embedded into `chroma_db_pro`.
3.  **Querying**:
    *   **Vector Search**: Finds the top 5 relevant chunks.
    *   **Context Injection**: The AI receives the relevant chunks + the **Master Catalog** of all files.
    *   **Answer**: The AI synthesizes a factual answer (Temperature=0).

## 🛠️ Troubleshooting

*   **"I don't see GPU usage"**: Ensure you are running `start_app.bat`. Check Task Manager -> Performance -> GPU -> **Compute/3D**.
*   **"List all articles" fails**: Ensure `metadata.json` exists. If not, run `python scripts/extract_metadata.py`.

## 📜 Credits

*   **Docling**: For superior PDF layout parsing.
*   **Ollama**: For local LLM inference.
*   **LangChain**: For the RAG framework.
*   **Streamlit**: For the user interface.
