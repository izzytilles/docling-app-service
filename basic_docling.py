import logging
from flask import Flask, request, jsonify
import utils
import psutil
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

app = Flask(__name__)

@app.before_first_request
def get_api_key():
    key_vault_name = os.getenv("KEY_VAULT_NAME")
    vault_uri = f"https://{key_vault_name}.vault.azure.net"
    secret_name = os.getenv("API_KEY_SECRET_NAME")
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_uri, credential=credential)
    retrieved_secret = client.get_secret(secret_name)

    expected_api_key = retrieved_secret.value
    app.config['API_KEY'] = expected_api_key # cache the key

def require_api_key(f):
    def wrapper(*args, **kwargs):
        user_api_key = request.headers.get("api-key")

        expected_api_key = app.config.get('API_KEY')
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
        user_query = request.get_json()
        if 'query' not in user_query:
            return "Please provide a query", 400
        
        query_text = user_query['query']
        query_keywords = utils.get_keywords(query_text)
        return jsonify(query_keywords), 200

    except Exception as e:
        logging.error(f"Error splicing query: {str(e)}")
        return f"Error: {str(e)}", 500

# for local flask app testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)