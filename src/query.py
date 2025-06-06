"""Script for querying the vector database."""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from pydantic import SecretStr

def setup_qa_chain():
    """Set up the QA chain with Pinecone and OpenAI."""
    load_dotenv()

    # Get API keys
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not pinecone_api_key or not openai_api_key:
        raise ValueError("API keys not set in .env file")

    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index("text-analyzer")

    # Set up OpenAI components
    embedding_model = OpenAIEmbeddings(api_key=SecretStr(openai_api_key))
    llm = ChatOpenAI(
        temperature=0, 
        api_key=SecretStr(openai_api_key),
        model="gpt-3.5-turbo"  # Faster and cheaper than GPT-4
    )

    # Create vector store and retriever
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embedding_model,
        text_key="text"
    )
    retriever = vector_store.as_retriever()

    # Create system prompt
    system_prompt = (
        "**You are an AI assistant that answers questions based only on the provided context from documents. **"
        "**Use the given context to answer the question accurately and do not hallucinate. **"
        "**If the context contains relevant information, provide a detailed answer. **"
        "**If the context doesn't contain relevant information to answer the question, **"
        "**respond with: 'This question is not relevant. **"
        "**Please ask questions related to the document content.' **"
        "**Context: {context}**"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Create document chain and retrieval chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain

def setup_qa_chain_with_history():
    """Set up the QA chain with conversation history support."""
    load_dotenv()

    # Get API keys
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not pinecone_api_key or not openai_api_key:
        raise ValueError("API keys not set in .env file")

    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index("text-analyzer")

    # Set up OpenAI components
    embedding_model = OpenAIEmbeddings(api_key=SecretStr(openai_api_key))
    llm = ChatOpenAI(
        temperature=0, 
        api_key=SecretStr(openai_api_key),
        model="gpt-3.5-turbo"
    )

    # Create vector store and retriever
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embedding_model,
        text_key="text"
    )
    retriever = vector_store.as_retriever()

    # Create system prompt with conversation history support
    system_prompt = (
        "**You are an AI assistant that answers questions based only on the provided context from documents. **"
        "**Use the given context to answer the question accurately and do not hallucinate. **"
        "**You have access to the conversation history to understand follow-up questions and provide contextually relevant answers. **"
        "**If the current question refers to something from previous messages, use that context appropriately. **"
        "**If the context contains relevant information, provide a detailed answer. **"
        "**If the context doesn't contain relevant information to answer the question, **"
        "**respond with: 'This question is not relevant. **"
        "**Please ask questions related to the document content.' **"
        "**Context: {context}**"
        "**Conversation History: {conversation_history}**"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Create document chain and retrieval chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain

def query_documents(question: str) -> str:
    """Query the vector database with a question."""
    qa_chain = setup_qa_chain()
    response = qa_chain.invoke({"input": question})

    # If the answer is empty, return a message saying the question is not relevant
    if len(response['answer']) == 0:
        return "This question is not relevant. Please ask relevant questions."
    return response['answer']

def query_documents_with_history(question: str, conversation_history: list) -> str:
    """Query the vector database with a question and conversation history."""
    qa_chain = setup_qa_chain_with_history()
    
    # Format conversation history for the prompt
    formatted_history = ""
    if conversation_history:
        formatted_history = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
            for msg in conversation_history
        ])
    
    response = qa_chain.invoke({
        "input": question,
        "conversation_history": formatted_history
    })

    # If the answer is empty, return a message saying the question is not relevant
    if len(response['answer']) == 0:
        return "This question is not relevant. Please ask relevant questions."
    return response['answer']

if __name__ == "__main__":
    # Example usage
    question = "What are the main requirements for the concrete mix design?"
    answer = query_documents(question)
    print("\nQuestion:", question)
    print("\nAnswer:", answer) 