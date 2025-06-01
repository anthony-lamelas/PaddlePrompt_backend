"""Main script for querying the vector database."""

import os
from dotenv import load_dotenv
from query import query_documents

def main():
    load_dotenv()
    
    # Example query
    question = "What is the best basketball player in the world?"
    answer = query_documents(question)
    
    print("\nQuestion:", question)
    print("\nAnswer:", answer)

if __name__ == '__main__':
    main() 