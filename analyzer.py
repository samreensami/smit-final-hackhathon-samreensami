import os
import google.generativeai as genai
from PIL import Image, ImageOps, ImageEnhance
import json
import re
import io
import sys
import traceback
from config import Config

# Force stable v1 API
os.environ['GOOGLE_GENAI_USE_V1'] = 'true'

class ReceiptAnalyzer:
    def __init__(self):
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in .env")
            
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception:
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')

    def preprocess_image(self, image_bytes):
        """Step 1: Optional Image Enhancement for better OCR."""
        img = Image.open(io.BytesIO(image_bytes))
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Apply enhancements
        img = ImageOps.grayscale(img).convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        return img

    def analyze(self, image_file_bytes):
        """Steps 2, 3 & 4: Extraction, Structuring, and Categorization."""
        try:
            # Step 1: Pre-process
            img = self.preprocess_image(image_file_bytes)
            
            # Step 2 & 3: Prompt for Structured Data
            prompt = """
            OCR this receipt and return a valid JSON object.
            
            CATEGORIES (Strictly use one of these): 
            [Food, Drink, Transport, Household, Entertainment, Other]

            JSON STRUCTURE:
            {
                "store_name": "string",
                "date": "string",
                "total": number,
                "items": [
                    {"name": "string", "qty": number, "price": number, "category": "category_name"}
                ],
                "advice": "Give a witty, sarcastic, yet helpful one-sentence budgeting tip based on these items."
            }
            Return ONLY the raw JSON.
            """

            response = self.model.generate_content([prompt, img])
            
            # Step 3: Data Cleaning (Regex for Markdown)
            raw_text = response.text.strip()
            clean_json = re.sub(r'```json|```', '', raw_text).strip()
            
            data = json.loads(clean_json)
            
            # Step 4: Categorization Sanitization
            valid_cats = ['Food', 'Drink', 'Transport', 'Household', 'Entertainment', 'Other']
            for item in data.get('items', []):
                if item.get('category') not in valid_cats:
                    item['category'] = 'Other'
            
            return data

        except Exception as e:
            print("\n" + "!"*60)
            print("❌ ANALYZER ERROR")
            traceback.print_exc(file=sys.stdout)
            print("!"*60 + "\n")
            return {"error": "AI Extraction Failed", "message": str(e)}