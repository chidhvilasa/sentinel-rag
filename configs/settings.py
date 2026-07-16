"""
Configuration management for Sentinel-RAG
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # LLM Settings
    llm_model: str = Field(default="llama3:8b")
    llm_base_url: str = Field(default="http://localhost:11434")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens: int = Field(default=2048)

    # Sentinel Model
    sentinel_model: str = Field(default="microsoft/deberta-v3-small")
    sentinel_threshold: float = Field(default=0.7)

    # Vector Database
    chroma_persist_dir: str = Field(default="./data/embeddings")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)

    # RAG Settings
    top_k_results: int = Field(default=5)

    # Evaluation
    attack_dataset_path: str = Field(default="./data/poisoned")
    clean_dataset_path: str = Field(default="./data/clean")
    results_output_path: str = Field(default="./results")

    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/sentinel.log")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
