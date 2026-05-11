import streamlit as st
import pandas as pd
import google.generativeai as genai

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

# --- Gemini Setup ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

def get_gemini_analysis(low_text, high_text):
    prompt = f"""
    Analyze these customer reviews for a product:
    
    LOW RATINGS (1-2 Stars):
    {low_text}
    
    HIGH RATINGS (3-5 Stars):
    {high_text}

    Return:
    1. **Executive Summary**: 2-sentence overview.
    2. **Top 3 Factors Causing Low Ratings**: List 3 factors with [Percentage]% and a brief explanation.
    3. **Recommendation**: One clear actionable step.
    """
    response = model.generate_content(prompt)
    return response.text

# --- UI ---
st.title("🚀 Review Insight Analyzer")

uploaded_file = st.file_uploader("Upload your Review CSV", type="csv")

if uploaded_file:
    # Added encoding='latin1' to handle the special characters in your sample
    df = pd.read_csv(uploaded_file, encoding='latin1')
    
    if 'rating' in df.columns and 'review_text' in df.columns:
        st.success(f"Loaded {len(df)} reviews.")
        
        if st.button("Analyze Differences"):
            # Filtering
            low_reviews = df[df['rating'] <= 2]['review_text'].dropna().astype(str).tolist()
            high_reviews = df[df['rating'] >= 3]['review_text'].dropna().astype(str).tolist()
            
            # Pulse Animation
            placeholder = st.empty()
            with placeholder.container():
                st.markdown('<div class="pulsing-circle">AI</div>', unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;'>Analyzing patterns...</p>", unsafe_allow_html=True)
            
            # API Call
            analysis = get_gemini_analysis("\n- ".join(low_reviews), "\n- ".join(high_reviews))
            placeholder.empty()
            
            # Results
            st.markdown("### 📊 Analysis Results")
            st.markdown(analysis)
            
            st.divider()
            st.write("📋 **Copy for Slack:**")
            st.code(f"*Review Analysis Report*\n\n{analysis}", language="markdown")
    else:
        st.error("CSV must have 'rating' and 'review_text' columns.")
