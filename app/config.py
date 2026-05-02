import os
from dotenv import load_dotenv

load_dotenv("../.env")


class Settings:
    def __init__(self):
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "")
        self.azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        self.azure_openai_embeddings_deployment = os.getenv(
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002"
        )
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        self.max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
        self.chunk_window_minutes = int(os.getenv("CHUNK_WINDOW_MINUTES", "5"))
        self.chunk_max_lines = int(os.getenv("CHUNK_MAX_LINES", "50"))
        self.max_chunks_for_llm = int(os.getenv("MAX_CHUNKS_FOR_LLM", "200"))


settings = Settings()
