import streamlit as st
import json
import pandas as pd
import os

# --- CONFIGURATION ---
LOG_FILE = "failed_queries.json"
DICT_FILE = "data/quran_dictionary.csv"
ADMIN_PASSWORD = "mizan_admin_secret" # Simple auth for prototype

st.set_page_config(page_title="Mizan Admin Dashboard", layout="wide")

st.title("🛡️ Mizan Admin Dashboard")
st.markdown("Review and approve vocabulary mappings from failed queries.")

# --- AUTHENTICATION ---
password = st.sidebar.text_input("Admin Password", type="password")
if password != ADMIN_PASSWORD:
    st.warning("Please enter the correct admin password to proceed.")
    st.stop()

# --- LOAD DATA ---
if not os.path.exists(LOG_FILE):
    st.info("No failed queries logged yet.")
    st.stop()

try:
    with open(LOG_FILE, "r") as f:
        failed_data = json.load(f)
except Exception as e:
    st.error(f"Error loading logs: {e}")
    st.stop()

# Filter pending
pending_items = [item for item in failed_data if item["status"] == "pending_review"]

if not pending_items:
    st.success("All queries reviewed! 🎉")
    st.stop()

st.markdown(f"### Pending Reviews ({len(pending_items)})")

# --- REVIEW INTERFACE ---
for i, item in enumerate(pending_items):
    with st.container():
        cols = st.columns([1, 2, 2, 1, 1])
        
        with cols[0]:
            st.text(item["timestamp"][:10])
            
        with cols[1]:
            st.markdown(f"**Query:** `{item['query']}`")
            
        with cols[2]:
            # Editable suggestion
            suggestion = st.text_input(f"Mapping for '{item['query']}'", value=item["suggestion"], key=f"s_{i}")
            
        with cols[3]:
            if st.button("✅ Approve", key=f"a_{i}"):
                # 1. Add to Dictionary
                try:
                    # Parse suggestion "Term -> Concept" or just take the value
                    # We'll assume the admin edits it to be the Definition
                    term = item['query']
                    definition = suggestion
                    
                    # Append to CSV
                    new_row = {
                        "title": term,
                        "subheading": "User Feedback",
                        "location": "",
                        "transliteration": term,
                        "translation": definition,
                        "arabic_verse_part": "",
                        "arabic_word": ""
                    }
                    
                    df = pd.read_csv(DICT_FILE)
                    new_df = pd.DataFrame([new_row])
                    final_df = pd.concat([df, new_df], ignore_index=True)
                    final_df.to_csv(DICT_FILE, index=False)
                    
                    # 2. Update Log Status
                    failed_data[failed_data.index(item)]["status"] = "approved"
                    with open(LOG_FILE, "w") as f:
                        json.dump(failed_data, f, indent=4)
                        
                    st.success(f"Added '{term}' to dictionary!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error saving: {e}")

        with cols[4]:
            if st.button("❌ Reject", key=f"r_{i}"):
                # Update Log Status
                failed_data[failed_data.index(item)]["status"] = "rejected"
                with open(LOG_FILE, "w") as f:
                    json.dump(failed_data, f, indent=4)
                st.rerun()
        
        st.divider()
