"""
Configuration management for the Insurance Claims Processing Agent.
Loads environment variables and provides centralized config access.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Azure Document Intelligence (Optional)
    azure_document_intelligence_endpoint: Optional[str] = None
    azure_document_intelligence_api_key: Optional[str] = None
    
    # Agent Configuration
    agent_max_iterations: int = 10
    agent_temperature: float = 0.7
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def has_document_intelligence(self) -> bool:
        """Check if Document Intelligence is configured."""
        return bool(
            self.azure_document_intelligence_endpoint 
            and self.azure_document_intelligence_api_key
        )


# Global settings instance
settings = Settings()
