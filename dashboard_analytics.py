import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from collections import Counter

st.set_page_config(page_title="Mizan Analytics", page_icon="📊", layout="wide")

st.title("📊 Mizan Flight Recorder")
st.markdown("### System Performance & Analytics")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Load Failed Queries
    failed_data = []
    if os.path.exists("failed_queries.json"):
        with open("failed_queries.json", "r") as f:
            try:
                failed_data = json.load(f)
            except:
                pass
    
    # Load Success Logs (Mocking for now as we haven't implemented success logging yet)
    # In a real app, we'd read from a database or log file.
    success_count = 120 # Mock
    
    return failed_data, success_count

failed_queries, success_count = load_data()

# --- METRICS ---
total_failed = len(failed_queries)
total_queries = success_count + total_failed
failure_rate = (total_failed / total_queries * 100) if total_queries > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Queries", total_queries)
col2.metric("Success Rate", f"{100 - failure_rate:.1f}%")
col3.metric("Failure Rate", f"{failure_rate:.1f}%", delta_color="inverse")

st.markdown("---")

# --- FAILED QUERIES ANALYSIS ---
st.subheader("❌ Failed Queries (Zero Results)")

if failed_queries:
    df_failed = pd.DataFrame(failed_queries)
    
    # Timeline
    if "timestamp" in df_failed.columns:
        df_failed["timestamp"] = pd.to_datetime(df_failed["timestamp"])
        daily_fails = df_failed.groupby(df_failed["timestamp"].dt.date).size().reset_index(name="count")
        fig = px.bar(daily_fails, x="timestamp", y="count", title="Failures Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Table
    st.dataframe(df_failed, use_container_width=True)
    
    # Word Cloud (Simple Frequency)
    st.subheader("☁️ Common Failure Topics")
    all_text = " ".join(df_failed["query"].tolist()).lower()
    words = [w for w in all_text.split() if len(w) > 3]
    word_counts = Counter(words).most_common(20)
    
    if word_counts:
        wc_df = pd.DataFrame(word_counts, columns=["Word", "Count"])
        fig2 = px.bar(wc_df, x="Word", y="Count", title="Top Words in Failed Queries")
        st.plotly_chart(fig2, use_container_width=True)
        
else:
    st.info("No failures recorded yet. The system is running smoothly! 🚀")

# --- DICTIONARY HEALTH ---
st.markdown("---")
st.subheader("📚 Dictionary Health")
# Count dictionary items
try:
    # This is a rough estimate, real count requires loading Chroma
    import chromadb
    client = chromadb.PersistentClient(path="./mizan_chroma_db")
    coll = client.get_collection("mizan_dictionary")
    dict_count = coll.count()
    st.metric("Total Dictionary Terms", dict_count)
except:
    st.warning("Could not connect to ChromaDB to count dictionary terms.")

st.markdown("---")
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Monitor Failure Rate**: If it spikes, check recent queries.
    2. **Analyze Topics**: Look for recurring words in failures (e.g., "Bitcoin", "IVF").
    3. **Update Dictionary**: Use `ingest_expansion.py` or `ingest_modern_terms.py` to add missing terms.
    """)
