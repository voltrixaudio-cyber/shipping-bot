import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DELHIVERY_API_TOKEN = os.getenv("DELHIVERY_API_TOKEN")
    
    # Base URLs
    DELHIVERY_STAGING_URL = "https://staging-express.delhivery.com"
    DELHIVERY_PROD_URL = "https://track.delhivery.com"
    
    # Use staging by default for safety unless explicitly set
    DELHIVERY_BASE_URL = os.getenv("DELHIVERY_API_URL", DELHIVERY_STAGING_URL)

    @classmethod
    def validate(cls):
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
        if not cls.DELHIVERY_API_TOKEN: missing.append("DELHIVERY_API_TOKEN")
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
