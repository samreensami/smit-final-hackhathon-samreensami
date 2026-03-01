import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from history_manager import save_to_history, load_history, clear_history

# Load environment variables
load_dotenv(override=True)

# --- APP CONFIGURATION ---
st.set_page_config(page_title="AI Receipt Intelligence", page_icon="🧾", layout="wide")

# Fetch API Key
# API Key ko Streamlit Secrets se uthayein
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ API Key nahi mili! Check karein ke .env file mein GOOGLE_API_KEY mojood hai.")
    st.stop()

# Configure Gemini
genai.configure(api_key=api_key.strip())

def get_supported_model():
    try:
        available_models = [m.name for m in genai.list_models()]
        targets = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest"]
        for target in targets:
            if target in available_models: return target
        return available_models[0] if available_models else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

def analyze_receipt(image_pil, model_name):
    prompt = """Analyze this receipt image. Return ONLY a valid JSON object:
    {
      "store": "Name",
      "date": "Date",
      "total": 0.0,
      "items": [{"name": "Item", "qty": 1, "price": 0.0, "category": "Food/Drinks/Others"}],
      "advice": "One witty budgeting tip"
    }
    Strictly return ONLY JSON."""
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, image_pil])
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "AI response was not in JSON format."}
    except Exception as e:
        return {"error": str(e)}

# --- UI INTERFACE ---
st.title("🧾 AI Receipt Intelligence")
active_model = get_supported_model()

# --- SIDEBAR: DATA LOADING & CALCULATION ---
st.sidebar.title("📊 Financial Summary")
history_data = load_history()

# Inialize variables (Errors se bachne ke liye)
grand_total = 0.0
receipt_count = 0
all_totals = []

if history_data:
    all_totals = [float(entry.get('total', 0)) for entry in history_data]
    grand_total = sum(all_totals)
    receipt_count = len(history_data)

# --- SIDEBAR: DISPLAY METRICS ---
if history_data:
    st.sidebar.metric("💰 Total Spent (All Time)", f"${grand_total:.2f}")
    st.sidebar.metric("📑 Total Receipts", receipt_count)
    
    if len(all_totals) > 1:
        st.sidebar.write("📈 Spending Trend")
        st.sidebar.line_chart(all_totals)
else:
    st.sidebar.info("No data yet. Analyze a receipt!")

# --- SIDEBAR: BUDGET ALERT SYSTEM ---
st.sidebar.divider()
st.sidebar.subheader("🎯 Budget Settings")
user_budget = st.sidebar.number_input("Set Monthly Budget ($)", min_value=1.0, value=1000.0)

if history_data:
    percentage_used = (grand_total / user_budget) * 100
    
    if percentage_used >= 100:
        st.sidebar.error(f"🚨 BUDGET EXCEEDED! ({percentage_used:.1f}%)")
        st.sidebar.warning("AI: Stop spending or start a side hustle!")
    elif percentage_used >= 80:
        st.sidebar.warning(f"⚠️ Warning: {percentage_used:.1f}% used.")
        st.sidebar.info("AI: You're getting dangerously close to being broke.")
    else:
        st.sidebar.success(f"✅ Safe: {percentage_used:.1f}% used.")
    
    st.sidebar.progress(min(percentage_used / 100, 1.0))

st.sidebar.divider()
st.sidebar.success(f"✅ Active Model: {active_model}")

# --- MAIN PAGE: UPLOAD ---
uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🖼️ Preview")
        st.image(image, use_container_width=True)
        
        if st.button("🚀 Analyze Receipt", use_container_width=True):
            with st.spinner("AI is thinking..."):
                result = analyze_receipt(image, active_model)
                if "error" in result:
                    st.error(f"Analysis Failed: {result['error']}")
                else:
                    st.session_state['receipt_data'] = result
                    save_to_history(result) 
                    st.success("✅ Saved to History!")
                    st.rerun()

    if 'receipt_data' in st.session_state:
        res = st.session_state['receipt_data']
        with col2:
            st.subheader(f"🏪 {res.get('store', 'Store')}")
            df = pd.DataFrame(res.get('items', []))
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.metric("Receipt Total", f"${res.get('total', 0.0):.2f}")
                fig = px.pie(df, values='price', names='category', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", data=csv, file_name="receipt.csv", mime='text/csv')
            
            st.info(f"💡 AI Advice: {res.get('advice')}")
else:
    st.info("Upload a receipt to get started.")

# --- SIDEBAR: HISTORY LIST ---
st.sidebar.divider()
st.sidebar.subheader("📜 History")
if st.sidebar.button("View Past Receipts"):
    if history_data:
        for idx, entry in enumerate(reversed(history_data)):
            with st.sidebar.expander(f"🧾 {entry.get('store')} ({entry.get('date')})"):
                st.write(f"**Total:** ${entry.get('total')}")
                if 'items' in entry:
                    st.dataframe(pd.DataFrame(entry.get('items')), hide_index=True)
    else:
        st.sidebar.info("No history.")

if st.sidebar.button("🗑️ Clear History"):
    clear_history()
    st.rerun()