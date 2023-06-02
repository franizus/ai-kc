import json
from langchain.chat_models import ChatOpenAI
import logging
from langchain.memory import MongoDBChatMessageHistory
from slack_sdk import WebClient
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chains import ConversationalRetrievalChain
import boto3
import pinecone
import requests
from functools import reduce
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logging.info(event)

    record = event["Records"][0]
    body = json.loads(record["body"])

    logging.info(body)

    try:
        OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
        SLACK_TOKEN = os.environ["SLACK_TOKEN"]
        PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
        PINECONE_API_ENV = os.environ["PINECONE_API_ENV"]
        JIRA_BASE_PATH = os.environ["JIRA_BASE_PATH"]
        JIRA_USER = os.environ["JIRA_USER"]
        JIRA_API_KEY = os.environ["JIRA_API_KEY"]
        index_name = "kushki-kb"

        llm = ChatOpenAI(
            temperature=0.1, openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo"
        )

        connection_string = os.environ["MONGO_CONNECTION_STRING"]

        message_history = MongoDBChatMessageHistory(
            connection_string=connection_string, session_id=body["user"]
        )

        # Upsert vectors to Pinecone Index
        pinecone.init(
            api_key=PINECONE_API_KEY,  # find at app.pinecone.io
            environment=PINECONE_API_ENV,
        )

        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        vectorstore = Pinecone.from_existing_index(index_name, embeddings)
        qa = ConversationalRetrievalChain.from_llm(llm, vectorstore.as_retriever())
        result = qa(
            {"question": body["text"], "chat_history": message_history.messages}
        )

        docs = vectorstore.similarity_search(body["text"])

        uriReferences = list()

        for doc in docs:
            if "imgUrl" in doc.metadata:
                uriReferences.append(doc.metadata["imgUrl"])

        message_history.add_user_message(body["text"])

        # ai_response = llm(message_history.messages)
        # message_history.add_ai_message(ai_response.content)

        message_history.add_ai_message(result["answer"])

        print(result["answer"])

        client = WebClient(token=SLACK_TOKEN)
        client.chat_postMessage(channel=body["channel"], text=result["answer"])

        if len(uriReferences) > 0:
            uniqueReferences = reduce(
                lambda re, x: re + [x] if x not in re else re, uriReferences, []
            )
            get_image_rs = requests.get(
                JIRA_BASE_PATH + uniqueReferences[0], auth=(JIRA_USER, JIRA_API_KEY)
            )

            if get_image_rs.status_code == 200:
                client.files_upload_v2(
                    channel=body["channel"],
                    initial_comment="Here is the file:",
                    filename="image.png",
                    content=get_image_rs.content,
                )

        json_response = {"respuesta": result["answer"]}

        client = boto3.client("lambda")
        client.invoke(
            FunctionName="slackResponse",
            Payload=json.dumps(
                {
                    "user": body["user"],
                    "text": body["text"],
                    "channel": body["channel"],
                    "answer": result["answer"],
                }
            ),
            InvocationType="Event",
        )

        return {"statusCode": 200, "body": json_response}
    except KeyError:
        print("Error")
        return {"statusCode": 400, "body": "Error"}
