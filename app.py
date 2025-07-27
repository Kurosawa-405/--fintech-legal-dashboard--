# 🏦 Fintech Gemini Dashboard with Fraud Detection

import streamlit as st
import pandas as pd
import feedparser
import os


try:
    from pyzbar.pyzbar import decode
    QR_SCANNING_ENABLED = True
except ImportError:
    QR_SCANNING_ENABLED = False

from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs

# 🌍 Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Initialize Gemini model
model = genai.GenerativeModel("gemini-1.5-pro")

# 🎛 App Config
st.set_page_config(page_title="Fintech Gemini Dashboard", layout="wide")
st.title("💼 FinanceHub")

# ------------------------
# 🔍 Fraud Detection Helper
# ------------------------
def is_upi_qr_suspicious(parsed_url):
    query_params = parse_qs(parsed_url.query)
    amount_str = query_params.get("am", [""])[0]
    vpa = query_params.get("pa", [""])[0]

    try:
        amount = float(amount_str) if amount_str else 0
    except ValueError:
        amount = 0

    suspicious = (
        amount > 50000 or
        "@" not in vpa or
        len(vpa) < 5 or
        vpa.endswith("@example") or
        not query_params.get("pn")
    )
    return suspicious

# ------------------------
# 📰 Fintech News Section
# ------------------------
@st.cache_data(show_spinner=False)
def fetch_rss_news():
    url = "https://news.google.com/rss/search?q=fintech&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    return pd.DataFrame([
        {"title": entry.title, "link": entry.link}
        for entry in feed.entries[:15]
    ])

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
def scan_uploaded_qr():
    st.subheader("📷 Fake UPI code Detector")

    if not QR_SCANNING_ENABLED:
        st.warning("🚫 QR code scanning is disabled: ZBar library not found in the environment.")
        return

    uploaded_file = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            st.write("🖼️ Image size:", image.size)

            decoded = decode(image)
            st.write("🔍 Raw decode output:", decoded)
        except Exception as e:
            st.error("Decode error during image processing.")
            st.code(str(e))
            return

        if decoded:
            data = decoded[0].data.decode("utf-8")
            st.success("✅ QR Code Detected")

            if data.startswith("upi://pay"):
                parsed_url = urlparse(data)
                query_params = parse_qs(parsed_url.query)

                # 🛡 Fraud Detection Logic
                if is_upi_qr_suspicious(parsed_url):
                    st.error("🚨 Suspicious UPI QR Detected! Transaction may be invalid or risky.")
                else:
                    st.success("✅ UPI QR appears safe.")

                # 🧾 Show UPI Fields
                st.markdown("### 💳 UPI Payment Details:")
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

with st.expander("📥 Scan UPI QR Code"):
    scan_uploaded_qr()

# ------------------------
# 🔗 UPI Payment Redirection Section
# ------------------------
st.subheader("🔗 Choose a UPI Payment Option")

upi_links = {
    "Paytm": "https://paytm.com/shop/payment",
    "PhonePe": "https://www.phonepe.com/",
    "GPay": "https://pay.google.com/",
    "Amazon Pay": "https://www.amazon.in/amazonpay/home"
}

col1, col2, col3, col4 = st.columns(4)
platforms = list(upi_links.keys())
cols = [col1, col2, col3, col4]

for i in range(4):
    with cols[i]:
        st.markdown(f"🡆 [{platforms[i]}]({upi_links[platforms[i]]})", unsafe_allow_html=True)

# ------------------------
# 📌 Footer
# ------------------------
st.caption("Built by Vansh 💼 using Gemini, Streamlit & FinTech magic ✨")
