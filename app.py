import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import time
import requests

# ScraperAPI integration
API_KEY = "YAHAN_APNI_SCRAPERAPI_KEY_DAALEIN" # <-- Apni API Key yahan paste karein

def get_amazon_price(asin):
    amazon_url = f"https://www.amazon.in/dp/{asin}"
    
    # ScraperAPI URL - Ye Amazon ko lagega ki alag-alag real laptops se request aa rahi hai
    payload = {
        'api_key': API_KEY, 
        'url': amazon_url, 
        'country_code': 'in', # Indian proxy ke liye
        'render': 'true' # Javascript load karne ke liye (Apparel prices ke liye zaroori)
    }
    
    try:
        response = requests.get('http://api.scraperapi.com', params=payload)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            price = None
            
            # Basic Price Checks
            price_element = soup.find("span", {"class": "a-price-whole"})
            if price_element:
                price = price_element.text.strip().replace(".", "")
            
            if not price:
                core_price_div = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"})
                if core_price_div:
                    offscreen = core_price_div.find("span", {"class": "a-offscreen"})
                    if offscreen:
                        price = offscreen.text.strip().replace("₹", "").replace(",", "")
            
            if price:
                return price
            else:
                return "Price Not Found (Shayad Size Select Karna Pade)"
                
        else:
            return f"API Error ({response.status_code})"
    except Exception as e:
        return "Connection Error"

# --- UI Setup ---
st.set_page_config(page_title="Amazon Bulk Price Fetcher PRO", layout="centered")
st.title("📦 Amazon Bulk ASIN Price Fetcher (PRO)")
st.markdown("ScraperAPI Powered - Bypasses Amazon CAPTCHA")

uploaded_file = st.file_uploader("Upload Template (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.upper()
    
    if 'ASIN' not in df.columns:
        st.error("❌ Uploaded file mein 'ASIN' column nahi mila.")
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
                
                price = get_amazon_price(clean_asin)
                prices.append(price)
                
                # ScraperAPI ke sath zyada delay ki zaroorat nahi hoti
                time.sleep(1) 
                progress_bar.progress((i + 1) / total_items)
            
            status_text.text("✅ Data Fetching Complete!")
            df['Fetched Price (₹)'] = prices
            
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Result CSV",
                data=csv,
                file_name="amazon_prices_result_pro.csv",
                mime="text/csv",
            )
