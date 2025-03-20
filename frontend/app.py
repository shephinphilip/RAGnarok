import chainlit as cl  # Import Chainlit for chat interface
import requests  # For making HTTP requests to backend
import os
import logging

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend service URL (assumes Docker container named 'fastapi' on port 8000)
BACKEND_URL = "http://fastapi:8000"

@cl.on_chat_start
async def start():
    """
    Initialize chat session and handle PDF file uploads.
    This function is triggered when a new chat session starts.
    """
    # Display welcome message and prompt for PDF uploads
    await cl.Message(content="Welcome! Please upload your PDFs to build the knowledge base.").send()
    
    # Request PDF files from user with a maximum of 10 files
    files = await cl.AskFileMessage(
        content="Upload PDFs",
        accept=["application/pdf"],
        max_files=10
    ).send()

    # Handle case when no files are uploaded or upload is cancelled
    if files is None or not files:
        await cl.Message(content="No files uploaded. Please try again.").send()
        return
    
    # Log received files for debugging
    logger.info(f"Files received: {[file.name for file in files]}")
    
    # Prepare files for multipart form data upload
    files_data = []
    for i, file in enumerate(files):
        with open(file.path, "rb") as f:
            files_data.append(("files", (file.name, f.read(), "application/pdf")))
    
    # Send files to backend service
    logger.info("Sending files to backend")
    response = requests.post(f"{BACKEND_URL}/upload_pdfs", files=files_data)
    logger.info(f"Backend response: {response.status_code} - {response.text}")
    
    # Handle backend response
    if response.status_code == 200:
        await cl.Message(content="PDFs uploaded and knowledge base built.").send()
    else:
        await cl.Message(content=f"Failed to upload PDFs: {response.status_code} - {response.text}").send()

@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming chat messages and get responses from backend.
    Args:
        message (cl.Message): The incoming chat message from the user
    """
    # Send user query to backend and get response
    response = requests.post(f"{BACKEND_URL}/chat", json={"query": message.content})
    
    # Process backend response
    if response.status_code == 200:
        answer = response.json()["answer"]
        await cl.Message(content=answer).send()
    else:
        await cl.Message(content=f"Error: Could not get response from backend: {response.text}").send()