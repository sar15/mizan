import streamlit as st
import brain
import os

# Page Config
st.set_page_config(
    page_title="Mizan - Islamic Fact-Checking AI",
    page_icon="⚖️",
    layout="centered"
)

# Title & Header
st.title("⚖️ Mizan")
st.subheader("Verifiable Islamic Knowledge Assistant")
st.markdown("---")

# Sidebar for API Key (Optional if set in env, but good for UI)
with st.sidebar:
    st.info("Ensure GROQ_API_KEY is set in your environment.")
    # Check if key is present
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
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 View Sources (Authentic References)"):
                for i, doc in enumerate(message["sources"]):
                    st.markdown(f"**Source {i+1}: {doc.metadata['surah_name']} ({doc.metadata['surah_num']}:{doc.metadata['verse_num']})**")
                    st.markdown(f"**Arabic:** {doc.metadata['arabic_text']}")
                    st.markdown(f"**Translation:** {doc.page_content}")
                    st.markdown(f"**Classic Translation:** {doc.metadata['classic_trans']}")
                    st.markdown(f"**Tafsir:** {doc.metadata['tafsir']}")
                    st.markdown("---")

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
                
                st.markdown(answer_text)
                
                # Add citation card immediately
                with st.expander("📚 View Sources (Authentic References)"):
                    for i, doc in enumerate(sources):
                        st.markdown(f"**Source {i+1}: {doc.metadata['surah_name']} ({doc.metadata['surah_num']}:{doc.metadata['verse_num']})**")
                        st.markdown(f"**Arabic:** {doc.metadata['arabic_text']}")
                        st.markdown(f"**Translation:** {doc.page_content}")
                        st.markdown(f"**Classic Translation:** {doc.metadata['classic_trans']}")
                        st.markdown(f"**Tafsir:** {doc.metadata['tafsir']}")
                        st.markdown("---")
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer_text,
                    "sources": sources
                })
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
