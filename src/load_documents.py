"""Script for loading PDFs into the vector database."""

import os
from dotenv import load_dotenv
import fitz
import tiktoken
import openai
from pinecone import Pinecone, ServerlessSpec

def load_pdfs_to_vectordb():
    """Load PDFs from the pdfs directory into Pinecone."""
    load_dotenv()

    folder_path = "./pdfs"
    
    # Initialize Pinecone
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY not set")
    
    pc = Pinecone(api_key=pinecone_api_key)
    index_name = "text-analyzer"

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
    
    index = pc.Index(index_name)

    # Process each PDF
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file)
            print(f"Processing: {file}")

            # Extract text
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()  # type: ignore

            # Chunk text
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            chunk_size = 800
            chunks = [encoding.decode(tokens[i:i + chunk_size]) 
                     for i in range(0, len(tokens), chunk_size)]

            # Generate embeddings
            embeddings = []
            for chunk in chunks:
                response = openai.embeddings.create(
                    input=chunk,
                    model="text-embedding-ada-002"
                )
                embeddings.append(response.data[0].embedding)

            # Save to Pinecone
            for i, vector in enumerate(embeddings):
                vector_id = f"{file.split('.')[0]}_chunk_{i}"
                chunk_metadata = {
                    "id": vector_id,
                    "source": file,
                    "chunk": i,
                    "text": chunks[i]
                }
                index.upsert(vectors=[(vector_id, vector, chunk_metadata)])

            print(f"Completed processing: {file}")

if __name__ == "__main__":
    load_pdfs_to_vectordb() 