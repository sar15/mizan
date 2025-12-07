import streamlit as st
import re
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Page Config
st.set_page_config(
    page_title="Project Mizan v3",
    page_icon="⚖️",
    layout="wide"
)

# ============ LAZY LOADING ============
@st.cache_resource
def get_rag_engine():
    from mizan_rag import RagEngine
    return RagEngine()

@st.cache_resource
def get_discovery_engine():
    from mizan_discovery import DiscoveryEngine
    return DiscoveryEngine()

# ============ HEADER ============
st.title("⚖️ Project Mizan v3 (Alpha)")
st.caption("The Balance: Quranic Truth Engine | Powered by BGE-M3 + Groq Llama 3.3")

# Initialize engines on first load
try:
    with st.spinner("Loading AI Models (first run may take a minute)..."):
        rag = get_rag_engine()
        discovery = get_discovery_engine()
    st.success("🟢 System Online", icon="✅")
except Exception as e:
    st.error(f"🔴 System Offline: {e}")
    st.stop()

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    show_evidence = st.checkbox("Show Raw Evidence", value=True)
    show_clusters = st.checkbox("Show Theme Clusters", value=True)
    results_limit = st.slider("Max Results", 5, 20, 10)
    st.divider()
    st.caption("Model: llama-3.3-70b-versatile")
    st.caption("Embedder: BAAI/bge-m3")

# ============ SEARCH BAR ============
query = st.text_input(
    "Ask a question about the Quran...",
    placeholder="e.g., What does the Quran say about patience?"
)

if query:
    # ============ PROCESSING ============
    with st.spinner("Consulting the Quran..."):
        # 1. Get RAG Answer
        try:
            answer = rag.answer_question(query)
        except Exception as e:
            answer = f"Error: {e}"
        
        # 2. Get Search Results for clustering
        try:
            results = rag.retriever.search(query, limit=results_limit)
            vectors = rag.retriever.get_vectors(results) if results else []
        except Exception as e:
            results = []
            vectors = []
    
    # ============ SECTION A: THE MUFASSIR ============
    st.markdown("---")
    st.subheader("📖 The Mufassir (Scholar's Answer)")
    
    # Style the answer
    is_error = "error" in answer.lower() or "cannot find" in answer.lower() or "intercepted" in answer.lower()
    
    if is_error:
        st.warning(answer)
    else:
        # Parse and display with citation highlighting
        # Replace <id> with styled badges
        styled_answer = re.sub(
            r'<([^>]+)>',
            r'`[\1]`',
            answer
        )
        st.markdown(styled_answer)
    
    # ============ SECTION B: THE EXPLORER ============
    if show_clusters and results and len(results) >= 3:
        st.markdown("---")
        st.subheader("🗺️ The Explorer (Theme Clusters)")
        
        try:
            clusters = discovery.cluster_results(results, vectors)
            
            if len(clusters) > 1 or "All Results" not in clusters:
                st.info(f"Found **{len(clusters)}** themes in these verses:")
                
                cols = st.columns(min(len(clusters), 3))
                for idx, (theme, items) in enumerate(clusters.items()):
                    with cols[idx % 3]:
                        with st.expander(f"**{theme}** ({len(items)} items)", expanded=False):
                            for item in items:
                                payload = item['payload']
                                content = payload.get('content', '')[:150]
                                doc_type = payload.get('type', 'verse')
                                icon = "📖" if doc_type == "verse" else "📚"
                                st.markdown(f"{icon} {content}...")
            else:
                st.caption("Not enough distinct themes to cluster.")
                
        except Exception as e:
            st.caption(f"Clustering unavailable: {e}")
    
    # ============ SECTION C: THE EVIDENCE ============
    if show_evidence and results:
        st.markdown("---")
        st.subheader("📜 The Evidence (Raw Sources)")
        st.caption(f"Showing top {len(results)} results by relevance")
        
        for idx, res in enumerate(results):
            payload = res['payload']
            score = res['score']
            doc_type = payload.get('type', 'verse')
            content = payload.get('content', '')
            original_id = payload.get('id', res['id'])
            
            # RTL detection
            is_arabic = bool(re.search(r'[\u0600-\u06FF]', content))
            direction = "rtl" if is_arabic else "ltr"
            align = "right" if is_arabic else "left"
            
            # Card styling
            border_color = "#4CAF50" if doc_type == "verse" else "#2196F3"
            icon = "📖 VERSE" if doc_type == "verse" else "📚 TAFSIR"
            
            with st.expander(f"{icon} | Score: {score:.3f} | ID: {original_id}", expanded=(idx < 2)):
                st.markdown(
                    f"""<div style="direction: {direction}; text-align: {align}; 
                    font-size: 1.05em; padding: 10px; 
                    border-left: 3px solid {border_color}; background: rgba(0,0,0,0.02);">
                    {content}
                    </div>""",
                    unsafe_allow_html=True
                )
                
                # Metadata
                meta = payload.get('metadata', {})
                if doc_type == 'verse':
                    st.caption(f"📍 Surah {meta.get('surah', '?')} : Ayah {meta.get('ayah', '?')}")
                else:
                    st.caption(f"🎓 Source: {meta.get('source', 'Ibn Kathir')}")

    # ============ NO RESULTS ============
    if not results:
        st.info("No matching verses found for this query.")

# ============ FOOTER ============
st.markdown("---")
st.caption("Project Mizan • Phase 3 Alpha • Built with BGE-M3, Groq, and Qdrant")
