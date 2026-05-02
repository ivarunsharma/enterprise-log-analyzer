from langchain_openai import AzureChatOpenAI
from app.config import settings

# Create LLM instances once at module level
llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_deployment=settings.azure_openai_deployment,
    api_version=settings.azure_openai_api_version,
    api_key=settings.azure_openai_api_key,
    temperature=0.0,
)

llm_creative = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_deployment=settings.azure_openai_deployment,
    api_version=settings.azure_openai_api_version,
    api_key=settings.azure_openai_api_key,
    temperature=0.2,
)
