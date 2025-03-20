import chainlit as cl
import requests

BACKEND_URL = "http://fastapi:8000"  # Docker service name

@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome! Please upload your PDFs to build the knowledge base.").send()
    files = await cl.AskFileMessage(
        content="Upload PDFs",
        accept=["application/pdf"],
        max_files=10
    ).send()
    # Prepare files for upload
    files_data = {file.name: (file.name, file.content, "application/pdf") for file in files}
    response = requests.post(f"{BACKEND_URL}/upload_pdfs", files=files_data)
    if response.status_code == 200:
        await cl.Message(content="PDFs uploaded and knowledge base built.").send()
    else:
        await cl.Message(content="Failed to upload PDFs.").send()

@cl.on_message
async def main(message: cl.Message):
    # Send query to backend
    response = requests.post(f"{BACKEND_URL}/chat", json={"query": message.content})
    if response.status_code == 200:
        answer = response.json()["answer"]
        await cl.Message(content=answer).send()
    else:
        await cl.Message(content="Error: Could not get response from backend.").send()