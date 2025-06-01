"""Test script for the Flask API."""

import requests
import json

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("-" * 50)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")

def test_query(question):
    """Test the query endpoint."""
    try:
        # Prepare the JSON payload
        payload = {"question": question}
        
        # Send POST request
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Query: {question}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("-" * 50)
        
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")

def main():
    """Run API tests."""
    print("Testing Flask API")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Test valid queries
    test_query("What is the best basketball player in the world?")
    test_query("Tell me about the proposal content")
    
    # Test edge cases
    test_query("")  # Empty question
    test_query("   ")  # Whitespace only
    
    print("Testing complete!")

if __name__ == "__main__":
    main() 