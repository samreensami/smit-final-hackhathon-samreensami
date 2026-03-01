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
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

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

# --- SIDEBAR: TOTAL SPENDING SUMMARY (NEW) ---
st.sidebar.title("📊 Financial Summary")
history_data = load_history()

if history_data:
    # Total kharcha calculate karna
    all_totals = [float(entry.get('total', 0)) for entry in history_data]
    grand_total = sum(all_totals)
    receipt_count = len(history_data)
    
    # Summary Metrics
    st.sidebar.metric("💰 Total Spent (All Time)", f"${grand_total:.2f}")
    st.sidebar.metric("📑 Total Receipts", receipt_count)
    
    # Chota sa bar chart sidebar mein (Spending per receipt)
    if len(all_totals) > 1:
        st.sidebar.write("📈 Spending Trend")
        st.sidebar.line_chart(all_totals)
else:
    st.sidebar.info("No data yet. Analyze a receipt to see your summary!")

st.sidebar.divider()
st.sidebar.success(f"✅ Active Model: {active_model}")

# --- MAIN PAGE: UPLOAD ---
uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🖼️ Receipt Preview")
        st.image(image, use_container_width=True)
        
        if st.button("🚀 Analyze Receipt", use_container_width=True):
            with st.spinner("AI is extracting data..."):
                result = analyze_receipt(image, active_model)
                
                if "error" in result:
                    st.error(f"Analysis Failed: {result['error']}")
                else:
                    st.session_state['receipt_data'] = result
                    save_to_history(result) 
                    st.success("✅ Analysis Done & Saved to History!")
                    st.rerun() # Refresh taake sidebar metrics update ho jayen

    if 'receipt_data' in st.session_state:
        res = st.session_state['receipt_data']
        with col2:
            st.subheader(f"🏪 {res.get('store', 'Store Name')}")
            st.caption(f"📅 Date: {res.get('date', 'N/A')}")
            
            df = pd.DataFrame(res.get('items', []))
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
                total_calc = df['price'].sum()
                st.metric("Receipt Total", f"${total_calc:.2f}")
                
                fig = px.pie(df, values='price', names='category', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", data=csv, file_name="receipt.csv", mime='text/csv')
            
            st.divider()
            st.info(f"💡 AI Advice: {res.get('advice', 'Keep saving!')}")
else:
    st.info("Upload a receipt to get started.")

# --- SIDEBAR: HISTORY ---
st.sidebar.divider()
st.sidebar.subheader("📜 Receipt History")

if st.sidebar.button("View Past Receipts"):
    if history_data:
        for idx, entry in enumerate(reversed(history_data)):
            store_name = entry.get('store', 'Unknown')
            date_val = entry.get('date', 'N/A')
            with st.sidebar.expander(f"🧾 {store_name} ({date_val})"):
                st.write(f"**Total:** ${entry.get('total')}")
                if 'items' in entry:
                    st.dataframe(pd.DataFrame(entry.get('items')), hide_index=True)
    else:
        st.sidebar.info("No history found.")

if st.sidebar.button("🗑️ Clear All History"):
    clear_history()
    st.sidebar.success("History Cleared!")
    st.rerun()