import streamlit as st
import os
import networkx as nx
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from pipeline import build_prime_pipeline, TheologicalGraph

# Load environment variables (fallback for local dev)
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Mizan Prime - The Verifiable Scholar",
    page_icon="⚖️",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f9f9f9;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        color: white;
    }
    .safe {
        background-color: #28a745;
    }
    .hallucination {
        background-color: #dc3545;
    }
    .citation-box {
        background-color: #e9ecef;
        padding: 10px;
        border-left: 5px solid #154360;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Title & Header
st.title("⚖️ Mizan Prime")
st.subheader("The Verifiable Islamic Knowledge Engine")
st.markdown("---")

# Sidebar: Brain Visualization
with st.sidebar:
    st.header("🧠 The Scholar's Mind")
    if st.button("View Knowledge Graph"):
        try:
            kg = TheologicalGraph()
            kg.build_from_json()
            
            # Simple Visualization
            fig, ax = plt.subplots(figsize=(8, 6))
            pos = nx.spring_layout(kg.graph)
            nx.draw(kg.graph, pos, with_labels=True, node_size=500, font_size=8, node_color="lightblue", ax=ax)
            st.pyplot(fig)
            st.success(f"Nodes: {kg.graph.number_of_nodes()} | Edges: {kg.graph.number_of_edges()}")
        except Exception as e:
            st.error(f"Could not visualize graph: {e}")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask a question (e.g., 'Ruling on missing prayer')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consulting the Iron Dome..."):
            try:
                # Initialize Pipeline
                app = build_prime_pipeline()
                
                # Run Pipeline
                result = app.invoke({
                    "question": prompt,
                    "retrieved_docs": [], "draft_answer": "", "grade": "", "final_output": ""
                })
                
                final_output = result["final_output"]
                grade = result["grade"]
                
                # Iron Dome Status
                with st.expander("🛡️ Iron Dome Status", expanded=True):
                    if grade == "SAFE":
                        st.markdown('<span class="status-badge safe">VERIFIED SOURCE</span>', unsafe_allow_html=True)
                        st.write("The answer is grounded in the verified database.")
                    else:
                        st.markdown('<span class="status-badge hallucination">INTERCEPTED BY GUARDIAN</span>', unsafe_allow_html=True)
                        st.write("The system detected a potential hallucination or lack of data.")
                
                # Display Answer
                st.markdown(final_output)
                
                # Show Citations (if safe)
                if grade == "SAFE" and result["retrieved_docs"]:
                    with st.expander("📚 Evidence"):
                        for doc in result["retrieved_docs"]:
                            st.markdown(f'<div class="citation-box">{doc}</div>', unsafe_allow_html=True)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": final_output})
                
            except Exception as e:
                st.error(f"System Error: {e}")
