"""Flask API server for the document query system."""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from query import query_documents

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Enable CORS for all domains on all routes (adjust as needed for production)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "API is running"})

@app.route('/query', methods=['POST'])
def query_endpoint():
    """
    Query endpoint that accepts JSON with question and returns JSON with answer.
    
    Expected JSON format:
    {
        "question": "Your question here"
    }
    
    Returns:
    {
        "question": "Your question here",
        "answer": "The generated answer",
        "status": "success"
    }
    """
    try:
        # Check if request contains JSON
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "status": "error"
            }), 400
        
        data = request.get_json()
        
        # Validate that question is provided
        if 'question' not in data:
            return jsonify({
                "error": "Missing 'question' field in request",
                "status": "error"
            }), 400
        
        question = data['question'].strip()
        
        # Validate that question is not empty
        if not question:
            return jsonify({
                "error": "Question cannot be empty",
                "status": "error"
            }), 400
        
        # Query the documents
        answer = query_documents(question)
        
        # Return successful response
        return jsonify({
            "question": question,
            "answer": answer,
            "status": "success"
        })
        
    except Exception as e:
        # Return error response
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500

@app.route('/query', methods=['GET'])
def query_get_info():
    """Information about the query endpoint."""
    return jsonify({
        "message": "Send a POST request with JSON containing a 'question' field",
        "example": {
            "question": "What is the best basketball player in the world?"
        },
        "endpoint": "/query",
        "method": "POST"
    })

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True  # Set to False in production
    ) 