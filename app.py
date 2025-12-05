import streamlit as st
import re
import warnings
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

# ============ CONFIGURATION ============
COLLECTION_NAME = "mizan_hybrid_v2"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
# Using the proven MiniLM model
DENSE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# =======================================

# Suppress Warnings
warnings.filterwarnings("ignore", category=UserWarning, module="fastembed")

st.set_page_config(page_title="Project Mizan", page_icon="⚖️", layout="centered")
st.title("⚖️ Project Mizan")
st.subheader("The Balance: Quranic Truth Engine")

def arabic_normalize(text):
    if not text: return ""
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    return text

def rrf_fusion_v2(dense_results, text_results, k=60):
    """
    Presentation Logic: Prioritizes Verses using an Interleaving Strategy.
    Rule: Show up to 2 Verses, then 1 Tafsir, repeat.
    """
    scores = {}
    
    # Helper to process hits
    def process(hits):
        for rank, hit in enumerate(hits):
            doc_id = hit.id
            if doc_id not in scores:
                scores[doc_id] = {
                    "hit": hit, 
                    "score": 0, 
                    "type": hit.payload.get('type', 'unknown')
                }
            scores[doc_id]["score"] += 1 / (k + rank + 1)

    process(dense_results)
    process(text_results)
    
    # Split into two lists
    verses = [v for v in scores.values() if v["type"] == "verse"]
    tafsirs = [v for v in scores.values() if v["type"] != "verse"]
    
    # Sort by score descending
    verses.sort(key=lambda x: x["score"], reverse=True)
    tafsirs.sort(key=lambda x: x["score"], reverse=True)
    
    # Interleave: 2 Verses -> 1 Tafsir
    result = []
    v_idx, t_idx = 0, 0
    
    while v_idx < len(verses) or t_idx < len(tafsirs):
        # Add up to 2 verses
        for _ in range(2):
            if v_idx < len(verses):
                result.append(verses[v_idx])
                v_idx += 1
        
        # Add 1 tafsir
        if t_idx < len(tafsirs):
            result.append(tafsirs[t_idx])
            t_idx += 1
            
    return result

@st.cache_resource
def get_resources():
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections()
        mode = "Server Mode"
    except:
        client = QdrantClient(path="qdrant_storage")
        mode = "Local Disk Mode"
        
    model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    return client, model, mode

try:
    client, dense_model, mode = get_resources()
    # Check if collection exists
    try:
        info = client.get_collection(COLLECTION_NAME)
        doc_count = f"{info.points_count:,}"
    except:
        doc_count = "Unknown"
        
    st.success(f"🟢 System Online ({mode}) | {doc_count} Documents", icon="✅")
except Exception as e:
    st.error(f"🔴 System Offline: {e}")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Filters")
    show_tafsir = st.checkbox("Show Tafsir Commentary", value=True)
    results_limit = st.slider("Max Results", 5, 50, 10)
    st.divider()
    st.caption(f"Model: {DENSE_MODEL_NAME}")

# Search Area
query = st.text_input("Ask a question...", placeholder="e.g., لا إكراه في الدين or treatment of parents")

if query:
    with st.spinner("Consulting the archives..."):
        try:
            # 1. Dense Search
            dense_vec = list(dense_model.embed([query]))[0]
            dense_hits = client.query_points(
                collection_name=COLLECTION_NAME,
                query=dense_vec,
                using="dense",
                limit=30
            ).points
            
            # 2. Keyword Search
            text_hits, _ = client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="searchable_text", match=models.MatchText(text=arabic_normalize(query)))]
                ),
                limit=30
            )
            
            # 3. Fusion (Interleaved)
            results = rrf_fusion_v2(dense_hits, text_hits)
            
            # Filter
            if not show_tafsir:
                results = [r for r in results if r['type'] == 'verse']
            
            # Render
            if results:
                st.markdown(f"Found **{len(results)}** matches for: *{query}*")
                
                for item in results[:results_limit]:
                    hit = item["hit"]
                    score = item["score"]
                    payload = hit.payload
                    doc_type = payload.get('type', 'unknown')
                    content = payload.get('content', '')
                    
                    # RTL Logic
                    is_arabic = bool(re.search(r'[\u0600-\u06FF]', content))
                    direction = "rtl" if is_arabic else "ltr"
                    align = "right" if is_arabic else "left"
                    
                    # Card
                    with st.expander(f"{'📖 VERSE' if doc_type == 'verse' else '📚 TAFSIR'} | Score: {score:.4f}", expanded=True):
                        st.markdown(
                            f"""<div style="direction: {direction}; text-align: {align}; font-size: 1.1em; padding: 10px; border-left: 3px solid {'#4CAF50' if doc_type=='verse' else '#2196F3'};">
                            {content}</div>""", 
                            unsafe_allow_html=True
                        )
                        
                        st.divider()
                        
                        if doc_type == 'verse':
                            meta = payload.get('metadata', {})
                            st.caption(f"📍 **Surah {meta.get('surah')} : Ayah {meta.get('ayah')}**")
                        else:
                            st.caption(f"🎓 **Source:** {payload.get('metadata', {}).get('source', 'Unknown')}")
            else:
                st.warning("No results found.")
                
        except Exception as e:
            st.error(f"Search Error: {e}")
