import streamlit as st
import time
from mlx_lm import load, generate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Mizan Scholar (Local M4)",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #2E86C1;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
MODEL_PATH = "mizan_fused"
CHROMA_PATH = "chroma_db_semantic"

# Prompts
INTERN_PROMPT = """You are a search optimizer. Convert the query into a single Islamic theological term.

Query: "money interest"
Term: Riba

Query: "washing before prayer"
Term: Wudu

Query: "fasting month"
Term: Ramadan

Query: "{input}"
Term:"""

SCHOLAR_PROMPT = """### Instruction:
You are an expert Islamic Scholar. Answer the following question using ONLY the provided context.

### Input:
{context}

### Question:
{question}

### Response:
"""

# --- RESOURCE LOADING (Cached) ---
@st.cache_resource
def load_engine():
    """Loads the Model and Database once and caches them."""
    print("🔄 Loading Resources...")
    start_time = time.time()
    
    # 1. Load Librarian
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(
        persist_directory=CHROMA_PATH, 
        embedding_function=embeddings,
        collection_name="mizan_knowledge_base"
    )
    
    # 2. Load Scholar
    model, tokenizer = load(MODEL_PATH)
    
    print(f"✅ Loaded in {time.time() - start_time:.2f}s")
    return vector_store, model, tokenizer

# --- MAIN APP ---
def main():
    st.title("🕌 Mizan Scholar")
    st.caption("Running Locally on Apple Silicon (M4) | MLX-Fused Llama 3")

    # Load Resources
    try:
        with st.spinner("Initializing Neural Engine & Library..."):
            vector_store, model, tokenizer = load_engine()
    except Exception as e:
        st.error(f"❌ System Error: {e}")
        st.stop()

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a theological question..."):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            debug_expander = st.expander("🧠 Thought Process (Intern & Librarian)", expanded=False)
            
            # --- STEP 1: THE INTERN ---
            with debug_expander:
                st.write("**1️⃣ Intern (Query Expansion):**")
                intern_input = INTERN_PROMPT.format(input=prompt)
                search_term = generate(
                    model, tokenizer, prompt=intern_input, max_tokens=20, verbose=False
                ).strip().split('\n')[0].replace('"', '').strip()
                st.code(f"Original: {prompt}\nOptimized: {search_term}")

            # --- STEP 2: THE LIBRARIAN ---
            with debug_expander:
                st.write("**2️⃣ Librarian (Retrieval):**")
                results = vector_store.similarity_search(search_term, k=5)
                
                # Fallback
                if not results:
                    st.warning("No results for term. Trying original query...")
                    results = vector_store.similarity_search(prompt, k=5)
                
                if results:
                    context_text = "\n\n".join([doc.page_content for doc in results])
                    citations = [doc.metadata.get('verse_id', 'Unknown') for doc in results]
                    st.success(f"Found {len(results)} verses.")
                    st.json(citations)
                    st.text_area("Context Preview", context_text, height=150)
                else:
                    st.error("No evidence found.")
                    context_text = ""
            
            # --- STEP 3: THE SCHOLAR ---
            if context_text:
                full_prompt = SCHOLAR_PROMPT.format(context=context_text, question=prompt)
                
                # Generate Response
                # Note: MLX streaming in Streamlit is tricky, using static generation for stability first
                response = generate(
                    model, tokenizer, prompt=full_prompt, max_tokens=512, verbose=False
                )
                
                # Stop Token Logic
                stop_tokens = ["<|eot_id|>", "### Instruction:", "### Input:", "### Question:"]
                for stop in stop_tokens:
                    if stop in response:
                        response = response.split(stop)[0]
                
                response = response.strip()
            else:
                response = "I cannot answer this question as no relevant context was found in the database."

            # Display Response
            response_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
