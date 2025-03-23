"""
Flask API for POC AI services
"""

import os
import time
import logging
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from services.bedrock_service import BedrockService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Initialize services
bedrock_service = BedrockService()

@app.route('/api/sql-query', methods=['POST', 'OPTIONS'])
def natural_language_sql():
    """
    Process a natural language query, convert it to SQL, and execute it.

    POST /api/sql-query
    """
    if request.method == 'OPTIONS':
        return make_response('', 200)

    try:
        # Get request data
        data = request.get_json()

        # Validate request
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter in request body'}), 400

        natural_language_query = data['query']

        # Validate query length
        if len(natural_language_query) < 5:
            return jsonify({'error': 'Query must be at least 5 characters long'}), 400

        # Process natural language to SQL query and execute
        start_time = time.time()
        result = bedrock_service.natural_language_to_sql_result(natural_language_query)
        processing_time = time.time() - start_time
        
        # Generate explanation if requested and if there's no error
        explanation = None
        if data.get('explain_results', False) and not result.get('error'):
            explanation = bedrock_service.explain_sql_results(result)

        # Return response
        response = {
            'natural_language_query': natural_language_query,
            'sql_query': result.get('sql_query'),
            'result': result.get('result', []),
            'row_count': result.get('row_count', 0),
            'column_names': result.get('column_names', []),
            'processing_time': processing_time
        }
        
        # Add explanation if available
        if explanation:
            response['explanation'] = explanation
            
        # Add error if present
        if result.get('error'):
            response['error'] = result.get('error')

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error processing natural language SQL query: {str(e)}")
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500