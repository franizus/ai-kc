import json
import logging
from typing import Dict, List, Union
from langchain.base_language import BaseLanguageModel
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import Pinecone
import pinecone
from langchain.document_loaders import (
    ConfluenceLoader,
    GoogleDriveLoader,
    WebBaseLoader,
)

from langchain.text_splitter import CharacterTextSplitter
from pymongo import MongoClient
import requests
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_API_ENV = os.environ["PINECONE_API_ENV"]
JIRA_BASE_PATH = os.environ["JIRA_BASE_PATH"]
JIRA_USER = os.environ["JIRA_USER"]
JIRA_API_KEY = os.environ["JIRA_API_KEY"]
MONGO_URI = os.environ["MONGO_CONNECTION_STRING"]


def build_response(body: Union[Dict, str], code: int):
    """Builds response for Lambda"""
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
        },
        "body": json.dumps(body),
    }


def splitDocs(docs, text="", isText: bool = False) -> List[str]:
    inputData = text
    if isText == False:
        inputData = docs[0].page_content
    text_splitter = CharacterTextSplitter(
        separator=" ", chunk_size=500, chunk_overlap=0
    )
    texts = text_splitter.split_text(text=inputData)
    logging.info("Splitted doc size: " + str(len(texts)))
    return texts


def getConfluence(pageId: str):
    pages = list()
    pages.append(pageId)
    rs = requests.get(
        JIRA_BASE_PATH + f"rest/api/content/{pageId}/child/attachment",
        auth=(JIRA_USER, JIRA_API_KEY),
    )
    attachments = rs.json()["results"]
    img_links = list()

    for attachment in attachments:
        if attachment["metadata"]["mediaType"] == "image/png":
            img_links.append(attachment["_links"]["download"])

    loader = ConfluenceLoader(
        url=JIRA_BASE_PATH,
        username=JIRA_USER,
        api_key=JIRA_API_KEY,
    )
    documents = loader.load(
        page_ids=pages, include_attachments=False, limit=1, max_pages=1
    )
    logging.info(f"Total documents: {len(documents)}")
    spittedDoc = splitDocs(documents)

    metadata = list()
    for text in spittedDoc:
        metadata_obj = {
            "origin": "Confluence",
            "id": documents[0].metadata["id"],
            "source": documents[0].metadata["source"],
            "title": documents[0].metadata["title"],
        }
        if len(img_links) > 0:
            metadata_obj["imgUrl"] = img_links[0]

        metadata.append(metadata_obj)

    return spittedDoc, metadata


def getGoogleDrive(pageId: str):
    pages = list()
    pages.append(pageId)
    loader = GoogleDriveLoader(
        document_ids=pages,
        credentials_path="./hackaton.json",
        token_path="./token.json",
    )
    documents = loader.load()
    logging.info(f"Total documents: {len(documents)}")
    return splitDocs(documents)


def getWebsite(url: str):
    loader = WebBaseLoader(url)
    documents = loader.load()
    logging.info(f"Total documents: {len(documents)}")
    return splitDocs(documents)


def getText(text: str):
    return splitDocs(None, text, True)


# def summarizeDocs(model: BaseLanguageModel, docs: List[Document]):
#     chain = load_summarize_chain(model, chain_type='map_reduce', verbose=False)
#     result = chain.run(docs)
#     return result


def insertPicone(docType: str, docs: List[str], metadata=None):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_API_ENV)
    index_name = "kushki-kb"
    if docType == "confluence":
        Pinecone.from_texts(
            [t for t in docs], embeddings, metadatas=metadata, index_name=index_name
        )
    else:
        Pinecone.from_texts(docs, embeddings, index_name=index_name)

    logging.info("Result pinecone: OK")
    return


def saveMongo(url: str):
    client = MongoClient(MONGO_URI)
    database = client["knowledge_base"]
    collection = database["info"]

    collection.insert_one({"url": url})


def handler(event, context=None):
    try:
        response = "Documentos cargados exitosamente"
        logging.info(event)
        body = json.loads(event["body"])
        logging.info(body)
        docType = body["type"]
        value = body["value"]
        url = body["url"]
        docs: List[Document] = None
        metadata = None
        logging.info(docType)

        if docType == "text":
            docs = getText(value)
        elif docType == "confluence":
            docs, metadata = getConfluence(value)
        elif docType == "website":
            docs = getWebsite(value)
        elif docType == "gdrive":
            docs = getGoogleDrive(value)

        saveMongo(url)
        insertPicone(docType, docs, metadata)
    except Exception as error:
        logging.error((error))
        return build_response(str(error), 500)

    return build_response(response, 200)


# if __name__ == "__main__":
#     handler({"body": """{"type": "text", "value": "https://www.google.com", "url": "test.com"}"""})

#!pip install atlassian-python-api
# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
