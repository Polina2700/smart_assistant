import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Google Cloud settings
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
    GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "global")
    DATA_STORE_ID = os.getenv("DATA_STORE_ID")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8001,http://127.0.0.1:8001"
    ).split(",")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "erp-chatbot-docs")
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Database
    DATABASE_URL = "sqlite:///./chat_logs.db"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            "GOOGLE_PROJECT_ID",
            "DATA_STORE_ID", 
            "GOOGLE_API_KEY"
        ]
        
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        print("Configuration loaded successfully")
        print(f"   Project: {cls.GOOGLE_PROJECT_ID}")
        print(f"   Data Store: {cls.DATA_STORE_ID}")

# Validate on import
Config.validate()