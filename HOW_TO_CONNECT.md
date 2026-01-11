# How to Use Google Colab GPU with Your Local Code

Additional setup is required because you want to **edit code locally** but **run the AI on Google's GPU**.

## The Concept: "Brain" vs. "Body"
*   **The Body (Your PC/Antigravity):** This is where your code lives (`main.py`, `agent_graph.py`). You edit files here. You run the application interface here.
*   **The Brain (Google Colab):** This is where the heavy AI models live. It provides the **GPU**.
*   **The Connection (Ngrok):** This acts as a cable connecting your PC to Google Colab.

## Step-by-Step Instructions

### 1. Set up the "Brain" (On Google Colab)
**Do this in your Web Browser.**
1.  Go to [Google Colab](https://colab.research.google.com/).
2.  Upload `agri_agent_colab.ipynb` (File -> Upload notebook).
3.  **Important:** Change Runtime to GPU (Runtime -> Change runtime type -> T4 GPU).
4.  Run all the cells in the notebook.
    *   *Why?* This installs the AI models on Google's servers.
    *   *Note:* It will ask for an **Ngrok Token**. Get it from [dashboard.ngrok.com](https://dashboard.ngrok.com) (it's free).
5.  At the end, it will give you a URL: `http://0.tcp.ngrok.io:12345`. **Copy this.**

### 2. Connect the "Body" (On Your PC)
**Do this in your Code Editor / Terminal.**
1.  Open your terminal.
2.  Paste the URL you copied to tell your code where the GPU is:
    *   **Windows:** `set OLLAMA_BASE_URL=http://0.tcp.ngrok.io:12345`
3.  Start your application:
    *   `python backend/main.py`
    
## Why did I get an error?
You got the `'apt-get' is not recognized` error because you tried to run Step 1 (The Brain setup) on your PC (The Body). Your PC typically runs Windows, but the setup script is written for Google's Linux computers. **You must run the `.ipynb` file on the Google Colab website.**
