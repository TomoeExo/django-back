import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Загрузка API ключа из переменных окружения
api_key = os.getenv('PROXY_API_KEY')
base_url = 'https://api.proxyapi.ru/openai/v1'

if not api_key:
    raise ValueError("PROXY_API_KEY is not set")

client = OpenAI(
    api_key="sk-vgLu1doy0UFV1BaLFtlsVFNTYcRMQylp",
    base_url="https://api.proxyapi.ru/openai/v1",
)
# Инициализация клиента OpenAI
client.api_key = api_key
client.base_url = base_url

def get_embedding(text: str):
    try:
        
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        if not embedding:
            raise ValueError("Error generating embedding.")
        return embedding
    except Exception as e:
        raise ValueError(f"Failed to get embedding: {e}")
