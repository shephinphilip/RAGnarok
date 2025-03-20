# RAGnarok

## Overview
RAGnarok is a Retrieval-Augmented Generation (RAG) chatbot that allows users to upload PDFs, build a knowledge base (KB), and ask questions or discuss topics based on the uploaded content. If the required information isn’t found in the KB, it performs a web search to augment its responses. Built from scratch without external frameworks like LangChain or LlamaIndex, it uses open-source tools, Groq for the language model (LLM), FastAPI for APIs, and Chainlit for the chat interface. The entire application is containerized with Docker for easy deployment.

## Features
- **PDF Processing:** Upload one or more PDFs to extract text and create a searchable knowledge base.
- **RAG Workflow:** Combines retrieval from the KB with web search augmentation for comprehensive answers.
- **Query Decomposition:** Breaks down complex user queries into sub-queries for better retrieval.
- **Web Search:** Uses Google Custom Search API (or an alternative like Brave API) when KB data is insufficient.
- **Open Source:** Built with pdfminer.six, sentence-transformers, FAISS, and Groq’s LLM.
- **Chat Interface:** Interactive UI powered by Chainlit.
- **API-Driven:** FastAPI backend for robust endpoints.
- **Dockerized:** Portable and scalable deployment.

## Architecture
The application is split into two main components:

### 1. FastAPI Backend
**Purpose:** Handles PDF uploads, builds the KB, and processes chat queries.

**Components:**
- **PDF Extraction:** Uses pdfminer.six to extract text from uploaded PDFs.
- **Knowledge Base:** Text is split into chunks, embedded with sentence-transformers (all-MiniLM-L6-v2), and indexed with FAISS for similarity search.
- **Query Processing:** Decomposes queries using Groq’s LLM, retrieves relevant KB passages, and performs web searches if needed.
- **Response Generation:** Groq’s LLM generates answers based on retrieved data.

**Endpoints:**
- `POST /upload_pdfs`: Upload PDFs and build the KB.
- `POST /chat`: Process user queries and return answers.

### 2. Chainlit Frontend
**Purpose:** Provides a user-friendly interface for uploading PDFs and chatting.

**Workflow:**
1. Upload PDFs via a file prompt.
2. Send queries to the FastAPI backend and display responses.

## Data Flow
1. User uploads PDFs through Chainlit.
2. FastAPI extracts text, builds the KB (FAISS index), and stores chunks.
3. User sends a query via Chainlit.
4. FastAPI decomposes the query, retrieves KB passages, augments with web search if needed, and generates a response with Groq.
5. Chainlit displays the response.

## Technologies Used
- **Backend:** FastAPI, Python 3.9
- **Frontend:** Chainlit
- **LLM:** Groq (mixtral-8x7b-32768 or available model)
- **Embedding:** sentence-transformers (all-MiniLM-L6-v2)
- **Vector Store:** FAISS (CPU)
- **PDF Processing:** pdfminer.six
- **Web Search:** Google Custom Search API
- **Containerization:** Docker, Docker Compose

## Prerequisites
- **Docker:** Installed and running (includes Docker Compose).
- **API Keys:**
  - Groq API Key: Sign up at Groq to get an API key.
  - Google API Key & CSE ID: Set up a Custom Search Engine at Google Cloud Console (free tier: 100 queries/day). Alternatively, use Brave API with a paid key.

## Setup Instructions
### 1. Clone the Repository
```bash
git clone <repository-url>
cd RAGnarok
```

### 2. Configure Environment Variables
Create a `.env` file in the project root with the following:
```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
```
Replace the placeholders with your actual keys.

### 3. Build and Run with Docker
```bash
docker-compose up --build
```
- **FastAPI Backend:** Runs on `http://localhost:8000`
- **Chainlit Frontend:** Runs on `http://localhost:8001`

### 4. Access the Chatbot
- Open `http://localhost:8001` in your browser.
- Follow the prompts to upload PDFs and start chatting.

## Usage
### Uploading PDFs
- On startup, Chainlit prompts you to upload PDFs (max 10 files, `.pdf` only).
- Upload one or more PDFs (e.g., research papers, manuals) to build the knowledge base.

### Asking Questions
- Type a question in the chat interface (e.g., "What is discussed in section X?" or "What’s the latest on Y?").
- The chatbot:
  - Decomposes the query into sub-queries.
  - Retrieves relevant passages from the KB.
  - Performs a web search if KB data is insufficient.
  - Generates and displays a response.

### Example Interaction
1. Upload a 50-page research paper PDF.
2. Ask: "What are the key findings?"
3. **Response:** The chatbot retrieves relevant sections from the PDF and summarizes them using Groq.

## Project Structure
```plaintext
RAGnarok/
├── fastapi/
│   ├── main.py           # FastAPI backend logic
│   ├── Dockerfile        # Dockerfile for backend
│   └── requirements.txt  # Backend dependencies
├── chainlit/
│   ├── app.py            # Chainlit frontend logic
│   ├── Dockerfile        # Dockerfile for frontend
│   └── requirements.txt  # Frontend dependencies
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Shared dependencies
└── README.md             # This file
```

## Dependencies
- **Backend:**
  - fastapi, uvicorn: Backend API framework and server.
  - sentence-transformers: Text embedding.
  - faiss-cpu: Vector similarity search.
  - pdfminer.six: PDF text extraction.
  - groq: LLM client.
  - google-api-python-client: Web search.
- **Frontend:**
  - chainlit: Chat interface.
  - requests: HTTP client for frontend-backend communication.

## Notes
- **KB Persistence:** The FAISS index is in-memory; for production, persist it to disk.
- **Web Search Limits:** Google’s free tier allows 100 queries/day. Consider Brave API for higher limits.
- **Performance:** Tested with large PDFs (50+ pages); adjust chunk size or similarity thresholds as needed.
- **Security:** CORS is set to allow all origins (`*`) for simplicity; restrict in production.

## Troubleshooting
- **API Key Errors:** Ensure `.env` is correctly set and loaded by Docker.
- **Port Conflicts:** Change ports in `docker-compose.yml` if `8000` or `8001` are in use.
- **No Response:** Check Docker logs (`docker-compose logs`) for errors.

## Contributing
Feel free to fork this repository, submit issues, or send pull requests to enhance functionality (e.g., adding persistent storage, improving decomposition logic).
