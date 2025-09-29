"""
Test script to check if Streamlit secrets are accessible
"""
import streamlit as st
import os

st.title("🔑 API Key Detection Test")

# Check different sources for API key
api_key_sources = []

# 1. Check Streamlit secrets
try:
    streamlit_key = st.secrets["OPENAI_API_KEY"]
    api_key_sources.append(("Streamlit Secrets", "✅ Found", streamlit_key[:8] + "..."))
except (KeyError, FileNotFoundError) as e:
    api_key_sources.append(("Streamlit Secrets", "❌ Not Found", str(e)))

# 2. Check environment variable
env_key = os.getenv('OPENAI_API_KEY')
if env_key:
    api_key_sources.append(("Environment Variable", "✅ Found", env_key[:8] + "..."))
else:
    api_key_sources.append(("Environment Variable", "❌ Not Found", "None"))

# 3. Check .env file
env_file_key = None
try:
    from dotenv import load_dotenv
    load_dotenv()
    env_file_key = os.getenv('OPENAI_API_KEY')
    if env_file_key:
        api_key_sources.append((".env File", "✅ Found", env_file_key[:8] + "..."))
    else:
        api_key_sources.append((".env File", "❌ Not Found", "None"))
except ImportError:
    api_key_sources.append((".env File", "⚠️ python-dotenv not installed", "N/A"))

# Display results
st.subheader("🔍 API Key Detection Results")

for source, status, value in api_key_sources:
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.write(f"**{source}:**")
    with col2:
        st.write(status)
    with col3:
        st.write(f"`{value}`")

# Determine which key to use
final_api_key = None
final_source = None

if api_key_sources[0][1] == "✅ Found":  # Streamlit secrets
    final_api_key = st.secrets["OPENAI_API_KEY"]
    final_source = "Streamlit Secrets"
elif env_key:  # Environment variable
    final_api_key = env_key
    final_source = "Environment Variable"
elif env_file_key:  # .env file
    final_api_key = env_file_key
    final_source = ".env File"

if final_api_key:
    st.success(f"🎉 Using API key from: **{final_source}**")
    st.info(f"Key preview: `{final_api_key[:8]}...{final_api_key[-4:]}`")
    
    # Test the API key with OpenAI
    st.subheader("🧪 API Key Validation Test")
    if st.button("Test OpenAI Connection"):
        with st.spinner("Testing OpenAI API connection..."):
            try:
                # Test the API key
                import openai
                openai.api_key = final_api_key
                
                # Make a simple API call
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                st.success("✅ OpenAI API key is valid and working!")
                
            except Exception as e:
                st.error(f"❌ API key test failed: {str(e)}")
else:
    st.error("❌ No valid API key found from any source")
    
    st.subheader("💡 How to Fix This:")
    st.markdown("""
    **For Streamlit Cloud apps:**
    1. Go to your app dashboard on Streamlit Cloud
    2. Click "Settings" → "Secrets" 
    3. Add: `OPENAI_API_KEY = "sk-your-key-here"`
    4. Save and redeploy
    
    **For local development:**
    1. Create `.env` file in project root
    2. Add: `OPENAI_API_KEY=sk-your-key-here`
    3. Restart the app
    
    **Or set environment variable:**
    ```bash
    export OPENAI_API_KEY=sk-your-key-here
    ```
    """)