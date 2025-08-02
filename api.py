"""Flask API server for the document query system."""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from src.query import query_documents_with_history

load_dotenv()

app = Flask(__name__)

conversation_sessions = {}

if os.environ.get('FLASK_ENV') == 'production':
    CORS(app, origins=[
        "https://paddleprompt.onrender.com",  
    ], 
    methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
    supports_credentials=True)
else:
    CORS(app, 
         origins="*", 
         methods=['GET', 'POST', 'OPTIONS'],  
         allow_headers=['Content-Type', 'Authorization'], 
         supports_credentials=True) 

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
    try:
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "status": "error"
            }), 400
        
        data = request.get_json()
        
        if 'question' not in data:
            return jsonify({
                "error": "Missing 'question' field in request",
                "status": "error"
            }), 400
        
        question = data['question'].strip()
        session_id = data.get('session_id', 'default')
        conversation_history = data.get('conversation_history', [])
        
        if not question:
            return jsonify({
                "error": "Question cannot be empty",
                "status": "error"
            }), 400
        
        MAX_WORDS = 500
        word_count = len(question.split())
        if word_count > MAX_WORDS:
            return jsonify({
                "error": f"Question too long. Maximum length is {MAX_WORDS} words. Current word count: {word_count}",
                "status": "error"
            }), 400
        
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
        
        conversation_sessions[session_id] = conversation_history[-10:]  # Last 10 messages (5 exchanges)
        
        answer = query_documents_with_history(question, conversation_sessions[session_id])
        
        conversation_sessions[session_id].extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ])
        
        return jsonify({
            "answer": answer,
            "status": "success"
        })
        
    except Exception as e:
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

    try:
        data = request.get_json() if request.is_json else {}
        session_id = data.get('session_id')
        
        if session_id:
            if session_id in conversation_sessions:
                del conversation_sessions[session_id]
                return jsonify({
                    "message": f"Session {session_id} cleared successfully",
                    "status": "success"
                })
            else:
                return jsonify({
                    "message": "Session not found",
                    "status": "success"  
                })
        else:
           
            import time
            current_time = time.time()
            sessions_to_remove = []

            if len(conversation_sessions) > 100:  
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
        "session_ids": list(conversation_sessions.keys())[:10],  
        "status": "success"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  
    ) 