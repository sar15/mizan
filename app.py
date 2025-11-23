import streamlit as st
import time
from mizan_core import app as mizan_app

# Page Config
st.set_page_config(
    page_title="Mizan: Fact, Not Fatwa",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("⚖️ Mizan: Fact, Not Fatwa")
st.caption("A Transparent 'Glass Box' AI for Quranic Reasoning")

# Sidebar: Brain Activity
st.sidebar.title("🧠 Brain Activity")
st.sidebar.markdown("---")

# Initialize Expanders (Placeholders)
exp_query = st.sidebar.expander("🔍 Query Analysis", expanded=False)
exp_evidence = st.sidebar.expander("📄 Evidence Retrieved", expanded=False)
exp_verification = st.sidebar.expander("✅ Verification Status", expanded=False)

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask a question about the Quran..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Placeholder for assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Reset Sidebar Expanders for new query
        exp_query.empty()
        exp_evidence.empty()
        exp_verification.empty()
        
        # Stream Logic
        inputs = {"question": prompt, "retry_count": 0}
        
        try:
            # We iterate through the graph updates
            for output in mizan_app.stream(inputs):
                
                # 1. Query Expansion
                if 'expand_query' in output:
                    new_state = output['expand_query']
                    expanded_q = new_state.get("question", "")
                    with exp_query:
                        st.markdown(f"**Original:** {prompt}")
                        st.markdown(f"**Expanded:** {expanded_q}")
                        st.success("Query Expanded")
                
                # 2. Retrieval
                if 'retrieve' in output:
                    new_state = output['retrieve']
                    docs = new_state.get("documents", [])
                    with exp_evidence:
                        if docs:
                            for i, doc in enumerate(docs):
                                st.markdown(f"**Doc {i+1}** ({doc.metadata.get('source_id', 'Unknown')}):")
                                st.caption(doc.page_content[:200] + "...") # Truncate for display
                                st.markdown("---")
                            st.success(f"Retrieved {len(docs)} documents")
                        else:
                            st.warning("No documents found.")
                
                # 3. Grading (Optional to show, but user asked for 3 specific expanders)
                # We can update Evidence expander if grading filters them out?
                if 'grade_documents' in output:
                    new_state = output['grade_documents']
                    decision = new_state.get("decision", "proceed")
                    filtered_docs = new_state.get("documents", [])
                    with exp_evidence:
                        st.info(f"Grading Decision: {decision.upper()}")
                        st.markdown(f"**Relevant Docs:** {len(filtered_docs)}")
                
                # 4. Generation (Intermediate)
                if 'generate' in output:
                    new_state = output['generate']
                    gen = new_state.get("generation", "")
                    # We don't display this yet, we wait for verification?
                    # Or we display it as draft?
                    # User said: "Display the final verified answer".
                    # So we hold off or show "Generating..."
                    message_placeholder.markdown("🤔 *Verifying answer...*")
                    
                # 5. Verification
                if 'verify_citations' in output:
                    new_state = output['verify_citations']
                    final_ans = new_state.get("generation", "")
                    
                    with exp_verification:
                        if "Verification Failed" in final_ans:
                            st.error("Verification Failed")
                            st.markdown(final_ans)
                        else:
                            st.success("Citations Verified")
                            st.markdown("All claims supported by context.")
                            
                    # Update main chat with final answer
                    full_response = final_ans
                    message_placeholder.markdown(full_response)
                    
            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
