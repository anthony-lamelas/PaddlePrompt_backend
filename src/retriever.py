"""Pinecone retrieval functionality."""

from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chains import RetrievalQA

class PineconeRetriever:
    def __init__(self, pinecone_api_key, openai_api_key):
        # pinecone connection
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = "text-analyzer"
        self.index = self.pc.Index(self.index_name)

        # openAi model and embeddings
        self.embedding_model = OpenAIEmbeddings(api_key=openai_api_key)
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