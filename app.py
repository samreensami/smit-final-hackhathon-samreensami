import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# --- APP CONFIGURATION ---
st.set_page_config(page_title="AI Receipt Intelligence", page_icon="🧾", layout="wide")

# Initialize Gemini Client (New SDK)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env file.")
    st.stop()

# Configure the GenAI SDK
genai.configure(api_key=api_key)

def get_supported_model():
    """Dynamically finds the correct model name to avoid 404 errors."""
    try:
        # List all models available to this API key
        available_models = [m.name for m in genai.list_models()]

        # Priority list of models to try
        targets = [
            "models/gemini-1.5-flash",
            "gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "gemini-1.5-flash-latest"
        ]

        for target in targets:
            if target in available_models:
                return target

        # If no specific flash model found, return the first one that supports generateContent
        return available_models[0] if available_models else "gemini-1.5-flash"
    except Exception as e:
        # Hard fallback
        return "gemini-1.5-flash"

def clean_json_response(text):
    """Extracts JSON from the AI response, handling markdown blocks."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group()
    return text.strip()

def analyze_receipt(image_pil, model_name):
    """Sends image to the discovered Gemini model."""
    prompt = """
    Analyze this receipt image. 
    Return ONLY a valid JSON object with the following keys:
    {
      "store": "Name of Store",
      "date": "Date of Receipt",
      "items": [
        {"name": "Item Name", "qty": 1, "price": 10.99, "category": "Food/Drinks/Others"}
      ],
      "advice": "A witty, sarcastic, but helpful one-sentence budgeting tip."
    }
    Strictly categorize every item into: Food, Drinks, or Others.
    If quantity is missing, use 1. Correct obvious OCR errors.
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, image_pil])
        
        if not response.text:
            return {"error": "AI returned an empty response."}
            
        cleaned_data = clean_json_response(response.text)
        return json.loads(cleaned_data)
        
    except Exception as e:
        return {"error": str(e)}

# --- UI LAYOUT ---
st.title("🧾 AI Receipt Intelligence (Auto-Discovery Mode)")
st.markdown("This version automatically finds the correct API endpoint for your region.")

# Diagnostic: Show active model
active_model = get_supported_model()
st.sidebar.success(f"✅ Active Model: {active_model}")

if st.sidebar.button("🔍 List All My Models"):
    models = [m.name for m in genai.list_models()]
    st.sidebar.write(models)

st.divider()

uploaded_file = st.file_uploader("📤 Upload Receipt Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    col_img, col_res = st.columns([1, 1])
    
    with col_img:
        st.subheader("🖼️ Uploaded Receipt")
        st.image(image, use_container_width=True)
        analyze_btn = st.button("🚀 Run AI Analysis", use_container_width=True)

    if analyze_btn:
        with st.spinner(f"🧠 Analysis in progress using {active_model}..."):
            result = analyze_receipt(image, active_model)
            
            if "error" in result:
                st.error(f"❌ Analysis Failed: {result['error']}")
                st.info("💡 Hint: If you see 404, click 'List All My Models' in the sidebar and check the terminal logs.")
            else:
                st.session_state['receipt_data'] = result
                st.success("✅ Analysis Complete!")

    if 'receipt_data' in st.session_state:
        data = st.session_state['receipt_data']
        items = data.get("items", [])
        
        if items:
            df = pd.DataFrame(items)
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(1)
            df['total'] = df['price'] * df['qty']
            
            with col_res:
                st.subheader(f"🏪 {data.get('store', 'Unknown Store')}")
                st.caption(f"📅 Date: {data.get('date', 'Unknown Date')}")
                
                total_val = df['total'].sum()
                cat_summary = df.groupby('category')['total'].sum().reset_index()
                top_cat = cat_summary.loc[cat_summary['total'].idxmax(), 'category']
                
                m1, m2 = st.columns(2)
                m1.metric("💰 Total Spent", f"${total_val:.2f}")
                m2.metric("🏆 Top Category", top_cat)
                
                st.markdown("#### 📋 Itemized Breakdown")
                st.dataframe(df[['name', 'qty', 'price', 'category', 'total']], use_container_width=True, hide_index=True)
                
                fig = px.pie(cat_summary, values='total', names='category', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                st.subheader("💡 AI Budgeting Tip")
                st.info(data.get("advice", "You're doing great!"))
else:
    st.info("👋 Welcome! Please upload a receipt image.")