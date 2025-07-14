import os
from dotenv import load_dotenv
load_dotenv()
# markdown imports
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

import tempfile
# semantic chunker imports
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import AzureOpenAIEmbeddings
# keyword extraction imports
import yake

def convert_file_to_markdown(uploaded_file):
    """
    Takes a file, converts it to markdown using Docling, and returns the markdown text
    Args:
        uploaded_file (FileStorage): The file to be processed, expected to be a DOCX or PDF file
    Returns:
        markdown_text (str): The converted markdown text from the file
    """
    # turn file into bytes 
    file_bytes = uploaded_file.read()
    binary_data = file_bytes

    # create a client for azure doc intelligence
    document_intelligence_client = DocumentIntelligenceClient(endpoint=os.getenv("DOC_INTELLIGENCE_ENDPOINT"), credential=AzureKeyCredential(os.getenv("DOC_INTELLIGENCE_KEY")))
    # set options for converter
    doc_to_analyze = AnalyzeDocumentRequest(bytes_source = binary_data)
    poller = document_intelligence_client.begin_analyze_document(
        model_id = "prebuilt-read",
        analyze_request = doc_to_analyze,
        output_content_format = "markdown"
    )
    result = poller.result()

    return result.content

def chunk_and_embed_file(uploaded_txt):
    """
    Takes text, embeds it using Azure OpenAI, then splits it into semantic chunks
    Args:
        uploaded_txt (str): The text to be processed, expected to be plaintext
    Returns:
        embedded_docs (list of dicts): A list of dicts, each containing a chunk of the original text and its embedding   
        in the format: [{"content": "plain text chunk", "embedding": [0.1, 0.2, ...]}, ...]
    
    Notes: With the Langchain chunking method, there is no way to retrieve the embedding straight from the semantic chunker.
        Possible future improvement is to manually do the semantic chunking to possibly reduce the number of calls to OpenAI embedder
        ALSO - this function assumes text is already in plaintext, so best practice is to call convert_file_to_markdown() first
    """
    # create embedder instance
    embedder = AzureOpenAIEmbeddings(
        model="text-embedding-3-large", 
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
        api_key=os.getenv("AZURE_OPENAI_KEY"), 
        api_version="2024-02-01"
    )
    # split text into semantic chunks
    text_splitter = SemanticChunker(embedder, 
                                    breakpoint_threshold_type ="standard_deviation")
    docs = text_splitter.create_documents([uploaded_txt])

    embeddings = embedder.embed_documents([doc.page_content for doc in docs])
    embedded_docs = [
        {"content": doc.page_content, "embedding": emb}
        for doc, emb in zip(docs, embeddings)
    ]
    return embedded_docs

def get_keywords(query):
    """
    Extracts keywords from the given query using Yake!

    Args:
        query (str): the query to analyze
    Returns:
        keywords (list of str): a list of keywords extracted from the query

    Notes:
        Yake! documentation: https://liaad.github.io/yake/docs/--home
        Number of keywords is set to half of the length of the query
    """
    num_keywords = int(len(query.split())/2)
    print(f"Extracting {num_keywords} keywords from query: {query}")
    kw_extractor = yake.KeywordExtractor(top=num_keywords)
    return [kw for kw, score in kw_extractor.extract_keywords(query)]