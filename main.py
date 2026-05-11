import streamlit as st
import pandas as pd
import requests
import json
import re
import time

# --- Page Config ---
st.set_page_config(page_title="Review Insight AI", page_icon="📈")

# --- CSS for Pulsing Animation ---
st.markdown("""
<style>
@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 20px rgba(255, 75, 75, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
}
.pulsing-circle {
    background: #ff4b4b; border-radius: 50%; width: 80px; height: 80px;
    margin: 30px auto; display: flex; align-items: center; justify-content: center;
    color: white; font-weight: bold; animation: pulse 1.5s infinite;
}
</style>
""", unsafe_allow_html=True)

# --- Function to Call Gemini API ---
def get_gemini_analysis(low_text, high_text, api_key):
    """Send reviews to Gemini and get analysis"""
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Analyze these customer reviews for a product:
    
    LOW RATINGS (1-2 Stars):
    {low_text[:4000]}
    
    HIGH RATINGS (3-5 Stars):
    {high_text[:4000]}

    Return your analysis in this exact format:

    **Executive Summary**: (2-sentence overview of why customers leave low ratings)
    
    **Top 3 Factors Causing Low Ratings**:
    - Factor 1: [XX%] - explanation
    - Factor 2: [XX%] - explanation
    - Factor 3: [XX%] - explanation
    
    **Recommendation**: One clear actionable step to improve the product.

    Make sure percentages add up to 100%. Be specific and analytical. Provide COMPLETE response.
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3
            # REMOVED: maxOutputTokens completely - let Gemini decide
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    result = response.json()
    text_response = result["candidates"][0]["content"]["parts"][0]["text"]
    
    return text_response

# --- UI ---
st.title("🚀 Review Insight Analyzer")
st.caption("Upload your customer reviews CSV to find out why customers give low ratings")

uploaded_file = st.file_uploader("Upload your Review CSV", type="csv")

if uploaded_file:
    # Try different encodings to handle special characters
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='latin1')
    
    # Check required columns
    if 'rating' in df.columns and 'review_text' in df.columns:
        st.success(f"✅ Loaded {len(df)} reviews")
        
        # Show preview
        with st.expander("Preview Data"):
            st.dataframe(df.head())
        
        # Show stats
        low_count = len(df[df['rating'] <= 2])
        high_count = len(df[df['rating'] >= 3])
        st.info(f"📊 Found {low_count} low ratings (1-2 stars) vs {high_count} high ratings (3-5 stars)")
        
        if st.button("🔍 Analyze Differences", type="primary"):
            
            # Get reviews
            low_reviews = df[df['rating'] <= 2]['review_text'].dropna().astype(str).tolist()
            high_reviews = df[df['rating'] >= 3]['review_text'].dropna().astype(str).tolist()
            
            # Take first 10 samples each (to save input tokens)
            low_sample = low_reviews[:10]
            high_sample = high_reviews[:10]
            
            low_text = "\n- ".join(low_sample)
            high_text = "\n- ".join(high_sample)
            
            # Pulse Animation
            placeholder = st.empty()
            with placeholder.container():
                st.markdown('<div class="pulsing-circle">AI</div>', unsafe_allow_html=True)
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1, text=f"Analyzing patterns... {i+1}%")
            
            try:
                # API Call
                api_key = st.secrets["GEMINI_API_KEY"]
                analysis = get_gemini_analysis(low_text, high_text, api_key)
                placeholder.empty()
                
                # Results
                st.markdown("### 📊 Analysis Results")
                
                # Display in a nice container
                st.markdown(analysis)
                
                st.divider()
                
                # Copy for Slack button
                if st.button("📋 Copy for Slack"):
                    st.toast("✅ Analysis copied to clipboard!", icon="✅")
                    st.code(analysis, language="markdown")
                    
            except Exception as e:
                placeholder.empty()
                st.error(f"Analysis failed: {str(e)}")
    else:
        st.error("CSV must have 'rating' and 'review_text' columns.")
else:
    st.info("👆 Upload a CSV file with 'rating' (1-5) and 'review_text' columns")
    
    # Show example format
    with st.expander("📋 Expected CSV Format"):
        st.markdown("""
        Your CSV should have these columns:
        - **rating**: 1 to 5 stars
        - **review_text**: The customer's review text
        
        Example:
        | rating | review_text |
        |--------|-------------|
        | 1 | "Battery dies too fast" |
        | 5 | "Amazing product!" |
        """)
