"""
Configuration settings for Pantree Subscribe & Save system.
"""
import os
from typing import Optional


class Config:
    """Main configuration class."""

    # Application Settings
    APP_NAME = "Pantree Subscribe & Save"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # API Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    # Vector Database Settings
    VECTORDB_HOST = os.getenv("VECTORDB_HOST", "localhost")
    VECTORDB_PORT = int(os.getenv("VECTORDB_PORT", "19530"))  # Milvus default
    VECTORDB_COLLECTION = os.getenv("VECTORDB_COLLECTION", "customer_purchases")
    VECTORDB_DIMENSION = int(os.getenv("VECTORDB_DIMENSION", "768"))  # Standard embedding size

    # Llama NIM Settings
    LLAMA_NIM_ENDPOINT = os.getenv("LLAMA_NIM_ENDPOINT", "http://localhost:8001")
    LLAMA_NIM_API_KEY = os.getenv("LLAMA_NIM_API_KEY", "")
    LLAMA_NIM_MODEL = os.getenv("LLAMA_NIM_MODEL", "meta/llama-3.1-8b-instruct")

    # AWS Sagemaker Settings
    SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "")
    SAGEMAKER_REGION = os.getenv("AWS_REGION", "us-west-2")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # Simulation Settings
    SIMULATION_MIN_PURCHASES = int(os.getenv("SIMULATION_MIN_PURCHASES", "3"))
    SIMULATION_MAX_PURCHASES = int(os.getenv("SIMULATION_MAX_PURCHASES", "20"))
    SIMULATION_MONTHS = int(os.getenv("SIMULATION_MONTHS", "6"))
    SIMULATION_STREAM_DELAY = float(os.getenv("SIMULATION_STREAM_DELAY", "0.5"))  # seconds

    # Frequency Analysis Settings
    FREQ_MIN_PURCHASES = int(os.getenv("FREQ_MIN_PURCHASES", "3"))
    FREQ_MIN_CONFIDENCE = float(os.getenv("FREQ_MIN_CONFIDENCE", "50.0"))
    FREQ_THRESHOLD_WEEKLY = int(os.getenv("FREQ_THRESHOLD_WEEKLY", "8"))
    FREQ_THRESHOLD_BIWEEKLY = int(os.getenv("FREQ_THRESHOLD_BIWEEKLY", "16"))
    FREQ_THRESHOLD_TRIWEEKLY = int(os.getenv("FREQ_THRESHOLD_TRIWEEKLY", "24"))

    # Dataset Paths
    LARGE_DATASET_PATH = os.getenv("LARGE_DATASET_PATH", "large_dataset")
    FICTIONAL_CUSTOMERS_PATH = os.getenv("FICTIONAL_CUSTOMERS_PATH", "fictional_customers")

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration settings.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required AWS settings for Sagemaker
        if not cls.SAGEMAKER_ENDPOINT:
            errors.append("SAGEMAKER_ENDPOINT is not set")

        # Warn about optional settings
        if not cls.LLAMA_NIM_API_KEY:
            print("Warning: LLAMA_NIM_API_KEY is not set (may be required)")

        return len(errors) == 0, errors

    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive values)."""
        print("="*60)
        print(f"{cls.APP_NAME} v{cls.VERSION} - Configuration")
        print("="*60)
        print(f"API: {cls.API_HOST}:{cls.API_PORT}")
        print(f"Vector DB: {cls.VECTORDB_HOST}:{cls.VECTORDB_PORT}")
        print(f"Llama NIM: {cls.LLAMA_NIM_ENDPOINT}")
        print(f"Sagemaker: {cls.SAGEMAKER_REGION}/{cls.SAGEMAKER_ENDPOINT[:20]}...")
        print(f"Debug Mode: {cls.DEBUG}")
        print("="*60)


# Create a singleton instance
config = Config()
