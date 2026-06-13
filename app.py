import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def get_amazon_price(asin):
    url = f"https://www.amazon.in/dp/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            price_element = soup.find("span", {"class": "a-price-whole"})
            
            if price_element:
                return price_element.text.strip().replace(".", "")
            else:
                return "Not Found/Out of Stock"
        else:
            return f"Blocked ({response.status_code})"
    except Exception as e:
        return "Error"

# --- UI Setup ---
st.set_page_config(page_title="Amazon Bulk Price Fetcher", layout="centered")
st.title("📦 Amazon Bulk ASIN Price Fetcher")
st.markdown("Apni CSV file upload karein jisme **`ASIN`** naam ka ek column ho.")

# File Uploader
uploaded_file = st.file_uploader("Upload Template (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    if 'ASIN' not in df.columns:
        st.error("❌ Uploaded file mein 'ASIN' column nahi mila. Kripya CSV check karein.")
    else:
        st.info(f"✅ Total ASINs found: {len(df)}")
        
        if st.button("🚀 Fetch Prices"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            prices = []
            total_items = len(df)
            
            for i, asin in enumerate(df['ASIN']):
                clean_asin = str(asin).strip()
                status_text.text(f"Fetching price for {clean_asin} ({i+1}/{total_items})...")
                
                # Fetch price
                price = get_amazon_price(clean_asin)
                prices.append(price)
                
                # Anti-block delay (2 seconds)
                time.sleep(2) 
                
                progress_bar.progress((i + 1) / total_items)
            
            status_text.text("✅ Data Fetching Complete!")
            df['Fetched Price (₹)'] = prices
            
            # Show Data
            st.dataframe(df)
            
            # Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Result CSV",
                data=csv,
                file_name="amazon_prices_result.csv",
                mime="text/csv",
            )
