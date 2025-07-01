import logging
from flask import Flask, request, jsonify
import utils

app = Flask(__name__)

@app.route("/markdown", methods=["POST"])
def convert_to_markdown():
    try:
        # get file name from request
        if 'file' not in request.files:
            return "Please upload a file", 400

        uploaded_file = request.files['file']
        markdown_text = utils.convert_file_to_markdown(uploaded_file)
        return markdown_text, 200, {'Content-Type': 'text/markdown'}
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route("/embedding", methods=["POST"])
def convert_to_embedding():
    try:
        # get file name from request
        if 'file' not in request.files:
            return "Please upload a file", 400

        uploaded_file = request.files['file']
        # MUST convert to markdown first
        markdown_text = utils.convert_file_to_markdown(uploaded_file)
        embedded_docs = utils.chunk_and_embed_file(markdown_text)
        return jsonify(embedded_docs), 200, {'Content-Type': 'application/json'}
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route("/keyword", methods=["POST"])
def extract_keywords():
    try:
        # get user query from query parameters
        user_query = request.args.get('query')
        if not user_query:
            return "Please provide a query", 400

        query_keywords = utils.get_keywords(user_query)
        return jsonify(query_keywords), 200
    
    except Exception as e:
        logging.error(f"Error splicing query: {str(e)}")
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)