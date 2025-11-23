import streamlit as st
import os
from dotenv import load_dotenv
from brain_v3 import build_scribe_graph

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Mizan - Islamic Fact-Checking AI",
    page_icon="⚖️",
    layout="centered"
)

# Custom CSS for Arabic Text
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400;1,700&display=swap');
    
    .arabic-text {
        direction: rtl;
        text-align: right;
        font-family: 'Amiri', serif;
        font-size: 26px;
        line-height: 2.0;
        color: #2E86C1;
        margin-bottom: 15px;
    }
    h1, h2, h3 {
        color: #154360;
    }
    .stMarkdown h2 {
        border-bottom: 2px solid #D4E6F1;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Title & Header
st.title("⚖️ Mizan 4.0")
st.subheader("The Verifiable Islamic Knowledge Engine")
st.markdown("---")

# Sidebar for API Key
with st.sidebar:
    st.info("Ensure GROQ_API_KEY is set in your environment.")
    if not os.getenv("GROQ_API_KEY"):
        api_key_input = st.text_input("Enter Groq API Key", type="password")
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input
            st.success("Key set!")
            st.rerun() # Rerun to update state immediately
        else:
            st.warning("API Key missing!")
            st.stop() # Stop execution until key is provided

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Render HTML content safely
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

# Input
if prompt := st.chat_input("Ask a question (e.g., 'Punishment for slander' or 'Verses about patience')..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Answer
    with st.chat_message("assistant"):
        with st.spinner("Consulting the Truth Vault..."):
            try:
                # Initialize Graph
                app = build_scribe_graph()
                
                # Initial State
                initial_state = {
                    "question": prompt,
                    "intent": "",
                    "retrieved_verse_ids": [],
                    "generated_json": {},
                    "final_display_html": ""
                }
                
                # Run Graph
                final_state = app.invoke(initial_state)
                html_output = final_state["final_display_html"]
                
                # Display
                st.markdown(html_output, unsafe_allow_html=True)
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": html_output
                })
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
