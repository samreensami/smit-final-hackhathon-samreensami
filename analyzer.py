import os
import google.generativeai as genai
from PIL import Image, ImageOps, ImageEnhance
import json
import re
import io
import sys
import traceback
from dotenv import load_dotenv

# Force load environment to ensure fresh key
load_dotenv(override=True)

class ReceiptAnalyzer:
    def __init__(self):
        # Directly fetch from OS to avoid config.py cache issues
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("❌ API Key missing! Check your .env file.")
            
        genai.configure(api_key=self.api_key)
        
        # Model switch: 'gemini-1.5-flash' is best for speed, 
        # but 'gemini-1.5-flash-latest' can sometimes bypass version errors
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        except Exception:
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def preprocess_image(self, image_bytes):
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Thori kam enhancement rakhein taaki AI asli text dekh sakay
        img = ImageEnhance.Contrast(img).enhance(1.2)
        return img

    def analyze(self, image_file_bytes):
        try:
            img = self.preprocess_image(image_file_bytes)
            
            # Refined prompt for more stable JSON
            prompt = """
            Extract receipt data into JSON. 
            Categories: [Food, Drink, Transport, Household, Entertainment, Clothes, Other]
            Format:
            {
                "store_name": "string",
                "date": "string",
                "total": number,
                "items": [{"name": "string", "qty": number, "price": number, "category": "string"}],
                "advice": "string"
            }
            Return ONLY JSON. No markdown.
            """

            # API Call
            response = self.model.generate_content([prompt, img])
            
            # Safety check for empty response
            if not response.text:
                return {"error": "AI returned empty text"}

            # Clean JSON
            clean_json = re.sub(r'```json|```', '', response.text).strip()
            data = json.loads(clean_json)
            
            # Sanitization
            valid_cats = ['Food', 'Drink', 'Transport', 'Household', 'Entertainment', 'Clothes', 'Other']
            for item in data.get('items', []):
                if item.get('category') not in valid_cats:
                    item['category'] = 'Other'
            
            return data

        except Exception as e:
            # Check for API Key specific errors
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "400" in err_msg:
                return {"error": "Invalid API Key", "message": "Google says your API key is wrong."}
            
            print("❌ ANALYZER ERROR:", err_msg)
            return {"error": "Processing Failed", "message": err_msg}