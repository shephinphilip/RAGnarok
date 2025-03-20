import chainlit as cl
import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://fastapi:8000"

@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome! Please upload your PDFs to build the knowledge base.").send()
    files = await cl.AskFileMessage(
        content="Upload PDFs",
        accept=["application/pdf"],
        max_files=10
    ).send()
    if files is None or not files:  # Handle cancel or no files
        await cl.Message(content="No files uploaded. Please try again.").send()
        return
    
    logger.info(f"Files received: {[file.name for file in files]}")
    files_data = []
    for i, file in enumerate(files):
        with open(file.path, "rb") as f:
            files_data.append(("files", (file.name, f.read(), "application/pdf")))
    
    logger.info("Sending files to backend")
    response = requests.post(f"{BACKEND_URL}/upload_pdfs", files=files_data)
    logger.info(f"Backend response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        await cl.Message(content="PDFs uploaded and knowledge base built.").send()
    else:
        await cl.Message(content=f"Failed to upload PDFs: {response.status_code} - {response.text}").send()

@cl.on_message
async def main(message: cl.Message):
    response = requests.post(f"{BACKEND_URL}/chat", json={"query": message.content})
    if response.status_code == 200:
        answer = response.json()["answer"]
        await cl.Message(content=answer).send()
    else:
        await cl.Message(content=f"Error: Could not get response from backend: {response.text}").send()