#!/usr/bin/env python3
"""Test script to verify the improvements to the query system."""

import requests
import json

def test_query_improvements():
    """Test various types of queries to see if the improvements work."""
    
    base_url = "http://localhost:5000"
    
    # Test cases that should now work better
    test_cases = [
        "What is concrete?",
        "Tell me about engineering design principles",
        "How do you build a canoe?",
        "What are the properties of concrete materials?",
        "Explain structural analysis",
        "What is the best basketball player in the world?",  # This should still be rejected
        "How do I make lasagna?",  # This should still be rejected
    ]
    
    print("Testing query improvements...")
    print("=" * 50)
    
    for i, question in enumerate(test_cases, 1):
        try:
            payload = {"question": question}
            
            response = requests.post(
                f"{base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\nTest {i}: {question}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer')
                print(f"Answer: {answer[:200]}...")
                
                # Check if it's still giving the old rejection message
                if "This question is not relevant" in answer:
                    print("⚠️  Still getting rejection message")
                else:
                    print("✅ Working better!")
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_query_improvements() 