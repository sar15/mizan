import streamlit as st
import graph_brain
import os

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Mizan ⚖️",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #F4F9F5; /* Soft White */
    }

    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* CUSTOM CLASSES */
    .source-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid #1E8449; /* Deep Emerald */
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .source-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }

    .card-header {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #1E8449;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .arabic-text {
        font-family: 'Amiri', serif;
        font-size: 28px;
        color: #1E8449;
        direction: rtl;
        text-align: right;
        line-height: 1.8;
        margin: 15px 0;
    }

    .translation-text {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        color: #444444;
        line-height: 1.6;
        font-style: italic;
        margin-top: 10px;
    }
    
    .tafsir-box {
        background-color: #f8f9fa;
        border-left: 3px solid #1E8449;
        padding: 10px;
        margin-top: 15px;
        font-size: 0.9rem;
        color: #444;
        max-height: 100px; /* Key fix: Limits height */
        overflow-y: auto;  /* Key fix: Adds scrollbar */
        border-radius: 4px;
        line-height: 1.6;
    }

    .context-badge {
        background-color: #e8f5e9;
        color: #1E8449;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* AGENT REASONING BOX */
    .agent-reasoning {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 15px;
        font-size: 14px;
        color: #555;
        margin-bottom: 15px;
    }
    
    /* CHAT MESSAGE STYLING */
    .stChatMessage {
        background-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("Mizan ⚖️")
    st.markdown("### The Agentic Islamic Scholar")
    
    st.markdown("---")
    
    st.markdown("#### About")
    st.info(
        """
        **Mizan** uses an advanced "Scholar Agent" architecture to answer queries based **strictly** on authentic sources.
        
        **Methodology:**
        1. **Dictionary Lookup**: Understands terminology.
        2. **Search**: Retrieves from Quran & Tafsir.
        3. **Grade**: Filters irrelevant results.
        4. **Answer**: Synthesizes evidence-based responses.
        """
    )
    
    st.markdown("---")
    
    with st.expander("⚙️ Settings"):
        api_key_input = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input
            
    st.markdown("---")
    st.warning(
        "**Disclaimer:** This is an AI Research tool designed for educational purposes. "
        "It is **not** a Fatwa center. Always consult qualified human scholars for personal rulings."
    )

# --- HELPER FUNCTION FOR SOURCES ---
def render_source_card(doc):
    surah = doc.metadata.get('surah_name', 'Source')
    ayah = doc.metadata.get('ayah_number', '')
    arabic = doc.metadata.get('arabic_text', '')
    content = doc.page_content
    source_id = doc.metadata.get('id', '')
    
    # Determine context label (e.g., Quran, Tafsir)
    is_quran = "surah" in str(source_id).lower()
    context_label = "Quran" if is_quran else "Tafsir/Hadith"
    
    # If it's Tafsir/Hadith, we might treat the content differently or just show it in the box
    # The requirement says: 
    # Verse: Large Arabic text (Green).
    # Translation: Italicized English.
    # Tafsir: Inside a gray box with the label "📜 Scholarly Context (Scroll to read)".
    
    # Assuming the 'content' field contains the English translation for Quran verses,
    # or the full text for Tafsir.
    
    html = f"""
    <div class="source-card">
        <div class="card-header">
            <span>{surah} {ayah}</span>
            <span class="context-badge">{context_label}</span>
        </div>
        <div class="arabic-text">{arabic}</div>
        <div class="translation-text">{content}</div>
    """
    
    # If we had separate Tafsir content, we would add it here. 
    # Since our current data model might mix them or we might want to treat long content as Tafsir:
    # Let's check if the content is very long, or if we have a specific field. 
    # For now, based on the user request, they want a "Tafsir" box. 
    # If the doc is purely Tafsir, maybe the whole thing goes in the box?
    # Or if it's a Quran verse, maybe we append a Tafsir section if available?
    # The user said: "Tafsir: Inside a gray box...".
    # Let's assume for now that if we have extra context or if it's a Tafsir doc, we use the box.
    
    # However, looking at the user's request: "Scrollable Source Text: Do not show the full Tafsir by default."
    # This implies that for Tafsir documents, the main content should be in the scrollable box.
    
    if not is_quran:
        # It's a Tafsir or other long text
        html = f"""
        <div class="source-card">
            <div class="card-header">
                <span>{surah} {ayah}</span>
                <span class="context-badge">{context_label}</span>
            </div>
            <div class="arabic-text">{arabic}</div>
            <div class="tafsir-box">
                <strong>📜 Scholarly Context (Scroll to read):</strong><br>
                {content}
            </div>
        </div>
        """
    else:
        # It's Quran
        html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

# --- MAIN CHAT AREA ---

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # 1. Show Reasoning (If Agent)
        if msg["role"] == "assistant" and "expanded_query" in msg:
            with st.expander("🧠 Agent Reasoning", expanded=False):
                st.markdown(f"""
                **1. Dictionary Lookup:** Analyzed terms in query.  
                **2. Search Query:** `{msg['expanded_query']}`  
                **3. Relevancy Check:** Filtered top results.
                """)
        
        # 2. Show Content
        st.markdown(msg["content"])
        
        # 3. Show Sources (If Agent)
        if msg.get("sources"):
            for doc in msg["sources"]:
                render_source_card(doc)

# --- INPUT & PROCESSING ---
if prompt := st.chat_input("Ask a question (e.g., 'Ruling on Interest', 'Story of Musa')..."):
    
    # 1. Check API Key
    if not os.environ.get("GROQ_API_KEY"):
        st.error("⚠️ Please enter your Groq API Key in the Settings sidebar to proceed.")
        st.stop()

    # 2. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Generate Agent Response
    with st.chat_message("assistant"):
        with st.spinner("Consulting the Library..."):
            try:
                # Run the Agent
                response = graph_brain.run_agent(prompt)
                
                # PART A: Agent Reasoning
                with st.expander("🧠 Agent Reasoning", expanded=True):
                     st.markdown(f"""
                    **1. Dictionary Lookup:** Analyzed terms in query.  
                    **2. Search Query:** `{response.get('expanded_query', prompt)}`  
                    **3. Relevancy Check:** Filtered top results.
                    """)
                
                # PART B: The Answer
                st.markdown(response["answer"])
                
                # PART C: Sources
                if response["sources"]:
                    st.markdown("### 📚 Authentic Sources")
                    for doc in response["sources"]:
                        render_source_card(doc)
                
                # Save to History
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": response["sources"],
                    "expanded_query": response.get("expanded_query")
                })
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
