# Mizan 4.0 Implementation Plan (Phase 4)

## Goal Description
Complete the system by adding Vector Search (ChromaDB) for general queries and integrating the new "Scribe" pipeline into the Streamlit frontend (`app.py`).

## User Review Required
> [!IMPORTANT]
> **Vector Search Fallback**: The system will now prioritize the Ontology (Golden Truths). If no concept is found, it will fallback to Semantic Search (ChromaDB) to retrieve relevant verses.
> **Frontend Overhaul**: `app.py` will be completely refactored to render the pre-generated HTML from `brain_v3.py`, ensuring consistent styling and verified text injection.

## Proposed Changes

### Vector Search
#### [NEW] [ingest_vectors.py](file:///Users/sarhanak/Documents/mizan/ingest_vectors.py)
- **Source**: `mizan_core.db` (quran_text table).
- **Target**: ChromaDB collection `quran_verified`.
- **Content**: English translation (Sahih) for embedding.
- **Metadata**: `verse_id`, `surah_number`, `ayah_number`.

### Backend Updates
#### [MODIFY] [mahkama.py](file:///Users/sarhanak/Documents/mizan/mahkama.py)
- **Add Method**: `search_vector_db(query)`
    - Queries `quran_verified` collection.
    - Returns list of `verse_id`s.

#### [MODIFY] [brain_v3.py](file:///Users/sarhanak/Documents/mizan/brain_v3.py)
- **Update Node**: `interpreter_node`
    - Logic: If `consult_ontology` returns empty, call `search_vector_db`.

### Frontend Integration
#### [MODIFY] [app.py](file:///Users/sarhanak/Documents/mizan/app.py)
- **Integration**: Use `brain_v3.build_scribe_graph`.
- **Rendering**: Display `final_display_html` using `st.markdown(..., unsafe_allow_html=True)`.
- **Styling**: Ensure Amiri font is loaded for Arabic text.

### Verification
#### [NEW] [verify_full_stack.py](file:///Users/sarhanak/Documents/mizan/verify_full_stack.py)
- **Test A**: "Slander" -> Ontology path.
- **Test B**: "Patience" -> Vector path.
- **Success Criteria**: Both return valid HTML output with verified text.

## Verification Plan
1. **Run `ingest_vectors.py`**: Verify ChromaDB creation.
2. **Run `verify_full_stack.py`**: Verify both search paths work.
3. **Manual Check**: Run `streamlit run app.py` (if possible/requested) to see UI.
