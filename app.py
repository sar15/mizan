import streamlit as st
import brain
import os

# Page Config
st.set_page_config(page_title="Mizan - Islamic Fact-Checking AI", page_icon="⚖️", layout="centered")

# Custom CSS for Arabic
st.markdown("""
    <style>
    .arabic-text { direction: rtl; text-align: right; font-family: "Amiri", serif; font-size: 26px; color: #1E8449; background: #f4f9f5; padding: 10px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ Mizan")
st.subheader("Verifiable Islamic Knowledge Assistant")
st.markdown("---")

# Sidebar
with st.sidebar:
    if not os.getenv("GROQ_API_KEY"):
        api_key_input = st.text_input("Enter Groq API Key", type="password")
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input
            st.success("Key set!")
    else:
        st.success("System Ready 🟢")

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Only show sources if they exist
        if msg.get("sources"):
            with st.expander(f"📚 View {len(msg['sources'])} Authentic Sources"):
                for doc in msg["sources"]:
                    st.markdown(f"**Surah {doc.metadata['surah']} ({doc.metadata['id']})**")
                    st.markdown(f'<div class="arabic-text">{doc.metadata["arabic"]}</div>', unsafe_allow_html=True)
                    st.markdown(f"_{doc.metadata['english']}_")
                    if doc.metadata['tafsir'] and doc.metadata['tafsir'] != "nan":
                         st.info(f"**Tafsir:** {doc.metadata['tafsir'][:300]}...")
                    st.divider()

# Input
if prompt := st.chat_input("Ask about the Quran (e.g., 'What is Zina?')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                response = brain.get_answer(prompt)
                st.markdown(response["answer"])
                
                # Only show expander if sources were found
                if response["sources"]:
                    with st.expander(f"📚 View {len(response['sources'])} Authentic Sources"):
                        for doc in response["sources"]:
                            st.markdown(f"**Surah {doc.metadata['surah']} ({doc.metadata['id']})**")
                            st.markdown(f'<div class="arabic-text">{doc.metadata["arabic"]}</div>', unsafe_allow_html=True)
                            st.markdown(f"_{doc.metadata['english']}_")
                            if doc.metadata['tafsir'] and doc.metadata['tafsir'] != "nan":
                                st.info(f"**Tafsir:** {doc.metadata['tafsir'][:300]}...")
                            st.divider()
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["answer"],
                    "sources": response["sources"]
                })
            except Exception as e:
                st.error(f"Error: {e}")
