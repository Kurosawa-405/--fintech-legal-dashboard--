import streamlit as st
import pandas as pd
import feedparser
import os
from PIL import Image
from pyzbar import pyzbar
from dotenv import load_dotenv
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs

# 🌍 Load environment variables 
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Initialize Gemini model
model = genai.GenerativeModel("gemini-1.5-pro")

# 📱 App Configuration
st.set_page_config(page_title="Fintech Gemini Dashboard", layout="wide")
st.title("💼 Fintech Dashboard: Gemini + UPI Scanner")

# ⏬ Fetch Fintech News
@st.cache_data(show_spinner=False)
def fetch_rss_news():
    url = "https://news.google.com/rss/search?q=fintech&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    return pd.DataFrame([
        {"title": entry.title, "link": entry.link}
        for entry in feed.entries[:15]
    ])

# 🧾 QR Scanner Function
def scan_uploaded_qr():
    st.subheader("📷 Upload UPI QR Code")
    uploaded_file = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        decoded = pyzbar.decode(image)
        
        if decoded:
            data = decoded[0].data.decode("utf-8")
            st.success("✅ QR Code Detected")

            if data.startswith("upi://pay"):
                st.markdown("### 🧾 UPI Payment Details:")
                parsed_url = urlparse(data)
                query_params = parse_qs(parsed_url.query)

                upi_fields = {
                    "Payee VPA (UPI ID)": query_params.get("pa", [""])[0],
                    "Payee Name": query_params.get("pn", [""])[0],
                    "Transaction Note": query_params.get("tn", [""])[0],
                    "Currency": query_params.get("cu", [""])[0],
                    "Amount": query_params.get("am", [""])[0]
                }

                for label, value in upi_fields.items():
                    if value:
                        st.markdown(f"**{label}:** {value}")

                if "pa" in query_params:
                    st.markdown("---")
                    st.markdown(f"🔗 [Copy & Pay via UPI](upi://pay?{parsed_url.query})", unsafe_allow_html=True)
            else:
                st.info("Scanned QR is valid but doesn't follow UPI format.")
        else:
            st.warning("⚠️ No QR code detected in the uploaded image.")

# ------------------------
# 📰 Fintech News Section
# ------------------------
with st.expander("📰 Fintech News & Gemini Legal Analysis"):
    news_df = fetch_rss_news()
    if news_df.empty:
        st.warning("News could not be fetched.")
    else:
        st.dataframe(news_df)

        with st.expander("📊 Analyze Headline with Gemini"):
            selected = st.selectbox("Choose a headline", news_df["title"])
            if st.button("Generate Insight"):
                with st.spinner("Thinking with Gemini..."):
                    prompt = f"Summarize this fintech headline and explain any legal or regulatory implications:\n\n{selected}"
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("### 🤖 Gemini Insight:")
                        st.write(response.text)
                    except Exception as e:
                        st.error("Gemini API Error")
                        st.code(str(e))

# ------------------------
# 💳 UPI QR Scanner Section
# ------------------------
with st.expander("📥 Scan UPI QR Code"):
    scan_uploaded_qr()
# ------------------------