import streamlit as st
import brain
import os

# Page Config
st.set_page_config(
    page_title="Mizan - Islamic Fact-Checking AI",
    page_icon="⚖️",
    layout="centered"
)

# Custom CSS for Arabic Text
st.markdown("""
<style>
    .arabic-text {
        direction: rtl;
        text-align: right;
        font-family: 'Amiri', 'Scheherazade', serif;
        font-size: 24px;
        color: #2E86C1;
    }
    .citation-header {
        font-weight: bold;
        color: #154360;
    }
</style>
""", unsafe_allow_html=True)

# Title & Header
st.title("⚖️ Mizan")
st.subheader("Verifiable Islamic Knowledge Assistant")
st.markdown("---")

# Sidebar for API Key
with st.sidebar:
    st.info("Ensure GROQ_API_KEY is set in your environment.")
    if not os.getenv("GROQ_API_KEY"):
        api_key_input = st.text_input("Enter Groq API Key", type="password")
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input
            st.success("Key set!")
        else:
            st.warning("API Key missing!")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.success(message["content"]) # Use success box for answer
            if "sources" in message:
                with st.expander("📚 View Authentic Sources"):
                    for i, doc in enumerate(message["sources"]):
                        st.markdown(f"**{doc.metadata['surah']} ({doc.metadata['id']})**")
                        st.markdown(f'<p class="arabic-text">{doc.metadata["arabic"]}</p>', unsafe_allow_html=True)
                        st.markdown(f"**English:** {doc.metadata['english']}")
                        st.markdown(f"**Tafsir:** {doc.metadata['tafsir'][:300]}...") # Snippet
                        st.markdown("---")
        else:
            st.markdown(message["content"])

# Input
if prompt := st.chat_input("Ask a question (English/Hinglish)..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Answer
    with st.chat_message("assistant"):
        with st.spinner("Consulting the knowledge base..."):
            try:
                response = brain.get_answer(prompt)
                answer_text = response["answer"]
                sources = response["sources"]
                
                st.success(answer_text)
                
                # Add citation card
                with st.expander("📚 View Authentic Sources"):
                    for i, doc in enumerate(sources):
                        st.markdown(f"**{doc.metadata['surah']} ({doc.metadata['id']})**")
                        st.markdown(f'<p class="arabic-text">{doc.metadata["arabic"]}</p>', unsafe_allow_html=True)
                        st.markdown(f"**English:** {doc.metadata['english']}")
                        st.markdown(f"**Tafsir:** {doc.metadata['tafsir'][:300]}...") # Snippet
                        st.markdown("---")
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer_text,
                    "sources": sources
                })
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
