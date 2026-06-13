import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import time
import cloudscraper

def get_amazon_price(asin):
    url = f"https://www.amazon.in/dp/{asin}"
    
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })
    
    try:
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            price = None
            
            # Check 1
            price_element = soup.find("span", {"class": "a-price-whole"})
            if price_element:
                price = price_element.text.strip().replace(".", "")
            
            # Check 2
            if not price:
                core_price_div = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"})
                if core_price_div:
                    offscreen = core_price_div.find("span", {"class": "a-offscreen"})
                    if offscreen:
                        price = offscreen.text.strip().replace("₹", "").replace(",", "")
                        
            # Check 3
            if not price:
                apex_price = soup.find("div", {"id": "apex_desktop"})
                if apex_price:
                    whole = apex_price.find("span", {"class": "a-price-whole"})
                    if whole:
                        price = whole.text.strip().replace(".", "")
            
            if price:
                return price
            else:
                return "Price Class Not Found"
                
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
    # CSV Load karna
    df = pd.read_csv(uploaded_file)
    
    # 🔴 SMART FIX: Har column name se extra space hatana aur UPPERCASE karna
    df.columns = df.columns.str.strip().str.upper()
    
    if 'ASIN' not in df.columns:
        st.error("❌ Uploaded file mein 'ASIN' column nahi mila.")
        st.warning(f"Aapki CSV mein ye columns mile hain: {', '.join(df.columns)}")
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
                
                time.sleep(4) 
                progress_bar.progress((i + 1) / total_items)
            
            status_text.text("✅ Data Fetching Complete!")
            df['Fetched Price (₹)'] = prices
            
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Result CSV",
                data=csv,
                file_name="amazon_prices_result.csv",
                mime="text/csv",
            )
