import os
from pinecone.grpc import PineconeGRPC as Pinecone
from dotenv import load_dotenv

load_dotenv()

# Загрузка API ключа из переменных окружения
api_key = os.getenv('PINECONE_API_KEY')

if not api_key:
    raise ValueError("PINECONE_API_KEY is not set")

# Инициализация клиента Pinecone
pinecone_client = Pinecone(api_key=api_key)
doc_index = pinecone_client.Index('gpt-viewing-calories')

def query_pinecone(index_name, vector, top_k=4, filter=None):
    try:
        response = doc_index.query(index=index_name, vector=vector, top_k=top_k, filter=filter)
        return response
    except Exception as e:
        raise ValueError(f"Failed to query Pinecone: {e}")
