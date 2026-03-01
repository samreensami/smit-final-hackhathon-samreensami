import os
from dotenv import load_dotenv

# .env file ko load karna (override=True ensures fresh values)
load_dotenv(override=True)

class Config:
    # Dono common names check karna
    GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # Secret key for Flask/Sessions
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    @staticmethod
    def validate():
        """Check if critical settings are missing before starting the app."""
        if not Config.GOOGLE_API_KEY:
            print("❌ ERROR: API Key missing in .env (Check GEMINI_API_KEY or GOOGLE_API_KEY)")
            return False
        
        # Check for spaces (Common cause for 400 error)
        if Config.GOOGLE_API_KEY and (" " in Config.GOOGLE_API_KEY.strip()):
            print("⚠️ WARNING: API Key contains spaces. This will cause 400 Invalid Key error.")
            
        return True