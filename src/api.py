"""Flask API server for the document query system."""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from query import query_documents_with_history

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# In-memory session storage (in production, use Redis or database)
conversation_sessions = {}

# Configure CORS based on environment
if os.environ.get('FLASK_ENV') == 'production':
    # Production: Allow your Render domains
    CORS(app, origins=[
        "https://paddleprompt.onrender.com",  # Your actual frontend URL
    ], 
    methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
    supports_credentials=True)
else:
    # Development: Allow all origins for Docker testing
    CORS(app, 
         origins="*",  # Allow all origins
         methods=['GET', 'POST', 'OPTIONS'],  # Allow these methods
         allow_headers=['Content-Type', 'Authorization'],  # Allow these headers
         supports_credentials=True)  # Support credentials if needed

# CORS handler for both development and production
@app.after_request
def after_request(response):
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers.add('Access-Control-Allow-Origin', 'https://paddleprompt.onrender.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "API is running"})

@app.route('/query', methods=['OPTIONS'])
def query_options():
    """Handle CORS preflight request for query endpoint."""
    return '', 200

@app.route('/query', methods=['POST'])
def query_endpoint():
    """
    Query endpoint that accepts JSON with question and conversation history.
    
    Expected JSON format:
    {
        "question": "Your question here (max 500 words)",
        "session_id": "unique_session_identifier",
        "conversation_history": [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
            {"role": "user", "content": "current question"}
        ]
    }
    
    Returns:
    {
        "answer": "The generated answer",
        "status": "success"
    }
    
    Error responses include word count if question exceeds limit.
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
        session_id = data.get('session_id', 'default')
        conversation_history = data.get('conversation_history', [])
        
        # Validate that question is not empty
        if not question:
            return jsonify({
                "error": "Question cannot be empty",
                "status": "error"
            }), 400
        
        # Validate question length (practical limit of 500 words)
        MAX_WORDS = 500
        word_count = len(question.split())
        if word_count > MAX_WORDS:
            return jsonify({
                "error": f"Question too long. Maximum length is {MAX_WORDS} words. Current word count: {word_count}",
                "status": "error"
            }), 400
        
        # Update session history
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
        
        # Store the conversation history (limit to last 10 exchanges to prevent context overflow)
        conversation_sessions[session_id] = conversation_history[-10:]  # Last 10 messages (5 exchanges)
        
        # Query the documents with conversation context
        answer = query_documents_with_history(question, conversation_sessions[session_id])
        
        # Add the new Q&A to session history
        conversation_sessions[session_id].extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ])
        
        # Return successful response
        return jsonify({
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

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """
    Clear a specific session or clean up old sessions.
    
    Expected JSON format:
    {
        "session_id": "session_to_clear"  // Optional: if not provided, clears old sessions
    }
    
    Returns:
    {
        "message": "Session cleared successfully",
        "status": "success"
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        session_id = data.get('session_id')
        
        if session_id:
            # Clear specific session
            if session_id in conversation_sessions:
                del conversation_sessions[session_id]
                return jsonify({
                    "message": f"Session {session_id} cleared successfully",
                    "status": "success"
                })
            else:
                return jsonify({
                    "message": "Session not found",
                    "status": "success"  # Not an error, session might have expired
                })
        else:
            # Clean up old sessions (keep only recent ones)
            import time
            current_time = time.time()
            sessions_to_remove = []
            
            # Remove sessions older than 24 hours (86400 seconds)
            # This is a simple cleanup - in production you'd store timestamps
            if len(conversation_sessions) > 100:  # Only cleanup if we have many sessions
                # Keep only the 50 most recent sessions
                session_items = list(conversation_sessions.items())
                sessions_to_keep = session_items[-50:]
                conversation_sessions.clear()
                conversation_sessions.update(sessions_to_keep)
                
                removed_count = len(session_items) - 50
                return jsonify({
                    "message": f"Cleaned up {removed_count} old sessions",
                    "status": "success"
                })
            
            return jsonify({
                "message": "No cleanup needed",
                "status": "success"
            })
            
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500

@app.route('/sessions-info', methods=['GET'])
def sessions_info():
    """Get information about active sessions."""
    return jsonify({
        "active_sessions": len(conversation_sessions),
        "session_ids": list(conversation_sessions.keys())[:10],  # Show first 10 for debugging
        "status": "success"
    })

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Set to False in production
    ) 