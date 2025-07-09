import os
from dotenv import load_dotenv
load_dotenv()
# markdown imports
from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import (
#     # PdfPipelineOptions,
#     # TesseractOcrOptions,
# )
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
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
    # download passed file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            uploaded_file.save(temp_file.name)

            # process the file to markdown
            # pipeline_options = PdfPipelineOptions()
            # pipeline_options.do_ocr = True
            # pipeline_options.do_table_structure = True
            # pipeline_options.table_structure_options.do_cell_matching = True
            # pipeline_options.ocr_options = TesseractOcrOptions()

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_cls=VlmPipeline,),
                }
            )
            # converter = DocumentConverter()
            result = converter.convert(temp_file.name).document

            markdown_text = result.export_to_markdown()
    return markdown_text

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
    """
    kw_extractor = yake.KeywordExtractor()
    return [kw for kw, score in kw_extractor.extract_keywords(query)]