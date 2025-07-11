import logging
from flask import Flask, request, jsonify
import utils
import psutil
import os

app = Flask(__name__)

def require_api_key(f):
    def wrapper(*args, **kwargs):
        expected_api_key = os.getenv("API_KEY")
        user_api_key = request.headers.get("x-api-key")
        if not user_api_key or user_api_key != expected_api_key:
            return "Invalid API Key", 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # for flask route registration
    return wrapper

@app.route("/")
def index():
    return "Welcome to the Docling converter API. Use /markdown, /embedding, or /keyword."

@app.route("/health")
def health_check():
    return "OK", 200

@app.route("/markdown", methods=["POST"])
@require_api_key
def convert_to_markdown():
    process = psutil.Process(os.getpid())

    try:
        # get file name from request
        if 'file' not in request.files:
            return "Please upload a file", 400

        uploaded_file = request.files['file']
        markdown_text = utils.convert_file_to_markdown(uploaded_file)

        if not markdown_text.strip():
            print("Empty markdown output")
            return "No content extracted from file.", 204  # no content

        return markdown_text, 200, {'Content-Type': 'text/markdown'}

    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route("/embedding", methods=["POST"])
@require_api_key
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
@require_api_key
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

# https://None@docling-converter-bsfvd4effgczbqbj.scm.canadacentral-01.azurewebsites.net/docling-converter.git
# curl -X POST -F "file=@/Users/isabeltilles/Downloads/testfile.pdf" https://docling-converter-bsfvd4effgczbqbj.canadacentral-01.azurewebsites.net/markdown
# curl -X POST docling-converter-bsfvd4effgczbqbj.canadacentral-01.azurewebsites.net/keyword?query=what+is+the+impact+of+climate+change+on+farming
# curl -X POST "http://0.0.0.0:8000/keyword?query=what+is+the+impact+of+climate+change+on+farming"
# curl -X POST -F "file=@/Users/isabeltilles/Downloads/testfile.pdf" http://0.0.0.0:8000/markdown

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)