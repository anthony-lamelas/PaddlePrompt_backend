"""Embedding generation functionality."""

import os
import tiktoken
import openai
from dotenv import load_dotenv

class EmbeddingGenerator:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
    def chunk_text_by_tokens(self, text, chunk_size, encoding_name="cl100k_base"):
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return [encoding.decode(tokens[i:i + chunk_size]) for i in range(0, len(tokens), chunk_size)]

    def generate_embeddings(self, chunks):
        embeddings = []
        for chunk in chunks:
            response = openai.embeddings.create(
                input=chunk,
                model="text-embedding-ada-002"
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    
    def process_text(self, text, chunk_size=1500):
        if not isinstance(text, str) or len(text) == 0:
            raise ValueError("Input text must be a non-empty string")
        chunks = self.chunk_text_by_tokens(text, chunk_size)
        embeddings = self.generate_embeddings(chunks)
        return chunks, embeddings 