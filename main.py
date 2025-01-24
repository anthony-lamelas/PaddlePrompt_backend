


import fitz
import os
import tiktoken
from dotenv import load_dotenv
import openai
from pinecone import Pinecone, ServerlessSpec

import langchain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chains import RetrievalQA



class PDFLoader:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        text = ""

        for page in doc:
            text += page.get_text()
        return text
    
# if __name__ == '__main__':
#     loader = PDFLoader("List_of_countries_by_air_pollution.pdf")
#     text = loader.extract_text()
#     print(text)
    


load_dotenv()

class EmbeddingGenerator:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
    # split into chunks by tokens
    def chunk_text_by_tokens(self, text, chunk_size, encoding_name="cl100k_base"):
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return [encoding.decode(tokens[i:i + chunk_size]) for i in range(0, len(tokens), chunk_size)]

    # generate embeddings for each chunk and return list of embeddings
    def generate_embeddings(self, chunks):
        embeddings = []
        for chunk in chunks:
            response = openai.embeddings.create(
                input=chunk,
                model="text-embedding-ada-002"
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    
    # split text into chunks and generate embeddings
    def process_text(self, text, chunk_size=1000):
        if not isinstance(text, str) or len(text) == 0:
            raise ValueError("Input text must be a non-empty string")
        chunks = self.chunk_text_by_tokens(text, chunk_size)
        embeddings = self.generate_embeddings(chunks)
        return chunks, embeddings

# if __name__ == "__main__":
#     generator = EmbeddingGenerator()
#     chunks, embeddings = generator.process_text(text, chunk_size=800)


class PineconeStore:

    def __init__(self, environmeent="us-east-1"):
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not set")
        
        # pinecone instance
        self.pc = Pinecone(ap_key=pinecone_api_key)
        self.index_name = "pdf-vector-store-pollution"

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

# if __name__ == "__main__":
#     vector_store = PineconeStore()
#     vector_store.save_vectors(embeddings, {"id": "doc_1", "source": "example.pdf"}, chunks)


class PineconeRetriever:
    def __init__(self, pinecone_api_key, openai_api_key):

        # pinecone connection
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = "pdf-vector-store-pollution"
        self.index = self.pc.Index(self.index_name)

        # openAi model and embeddings
        self.embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = OpenAI(temperature=0, api_key=openai_api_key)

        # create the Pinecone vector store
        self.vector_store = PineconeVectorStore(index=self.index, embedding=self.embedding_model, text_key="text")
        self.retriever = self.vector_store.as_retriever()

        # create the RetrievalQA chain
        self.qa_chain = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.retriever)

    def query(self, query_text):
        # execute the QA chain with the input query
        response = self.qa_chain.invoke({"query": query_text})
        return response['result']


if __name__ == '__main__':

    folder_path = "./pdfs"
    generator = EmbeddingGenerator()
    vector_store = PineconeStore()

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file)
            print(f"Processing: {file}")

            loader = PDFLoader(pdf_path)
            text = loader.extract_text()

            chunks, embeddings = generator.process_text(text, chunk_size=800)
            metadata = {"id": file.split(".")[0], "source": file}
            vector_store.save_vectors(embeddings, metadata, chunks)
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    retriever = PineconeRetriever(pinecone_api_key=pinecone_api_key, openai_api_key=openai_api_key)
    user_input = input("Message AirScopeAI: ")
    result = retriever.query(f"{user_input} || Make the response a maximum of 4 sentences.")
    print(result)