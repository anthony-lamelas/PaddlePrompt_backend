"""Pinecone vector store functionality."""

import os
from pinecone import Pinecone, ServerlessSpec

class PineconeStore:
    def __init__(self, environmeent="us-east-1"):
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not set")
        
        # pinecone instance
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = "text-analyzer"

        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
    
    def save_vectors(self, vectors, metadata, chunks):
        index = self.pc.Index(self.index_name)

        # save each embedding with unique metadata
        for i, vector in enumerate(vectors):
            vector_id = f"{metadata['id']}_chunk_{i}" # uniqe id
            chunk_metadata = {
                "id": vector_id,
                "source" : metadata["source"],
                "chunk" : i,
                "text": chunks[i]
            }

            index.upsert(vectors=[(vector_id, vector, chunk_metadata)])

    def delete(self):
        index = self.pc.Index(self.index_name)
        index.delete(delete_all=True) 