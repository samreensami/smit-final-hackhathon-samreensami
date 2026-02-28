import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load .env file explicitly
load_dotenv()

# 2. Check for both common key names
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

def test_gemini():
    if not api_key:
        print("❌ ERROR: API Key (GOOGLE_API_KEY or GEMINI_API_KEY) not found in .env file.")
        print("💡 Tip: Rename '.env.example' to '.env' and paste your key there.")
        return

    print(f"🔑 Testing API Key: {api_key[:5]}...{api_key[-5:]}")

    try:
        # Configure the SDK
        genai.configure(api_key=api_key)
        
        print("--- Model Availability Check ---")
        # List models to verify connection
        available_models = [m.name for m in genai.list_models()]
        print("✅ Successfully connected to Google API.")
        
        # Checking for the specific model
        target_model = 'models/gemini-1.5-flash'
        if target_model in available_models:
            print(f"✅ {target_model} is AVAILABLE for this key.")
        else:
            print(f"⚠️ {target_model} not found. Available models: {available_models[:3]}...")

        print("--- Simple Text Generation Test ---")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, are you active?")
        
        if response.text:
            print(f"✅ AI Response: {response.text}")
            print("\n🎉 YOUR API KEY IS WORKING PERFECTLY!")
            
    except Exception as e:
        if "400" in str(e):
            print(f"❌ Connection Failed (400): Your API Key is likely invalid or expired.")
        elif "API_KEY_INVALID" in str(e):
            print(f"❌ Error: The API Key provided is not recognized by Google.")
        else:
            print(f"❌ Error Details: {e}")

if __name__ == "__main__":
    test_gemini()