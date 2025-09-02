# pages/2_Chunk_Document.py
import os
import streamlit as st
from chunking import HierarchicalChunker, get_chunking_analysis

DATA_DIR = "data"

def load_documents():
    docs = {}
    for fname in os.listdir(DATA_DIR):
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    docs[fname] = f.read()
            except Exception:
                st.warning(f"Could not read {fname}. Skipping...")
    return docs

def main():
    st.title("📄 Document Chunking & Analysis")

    docs = load_documents()
    if not docs:
        st.info("No documents found. Upload files first.")
        return

    st.sidebar.header("⚙️ Chunking Options")
    doc_name = st.sidebar.selectbox("Choose a document", list(docs.keys()))

    strategy = st.sidebar.radio(
        "Chunking Strategy",
        ["Hierarchical", "Hierarchical with Overlap", "Fixed-size"]
    )

    # Strategy-specific parameters
    paragraph_overlap = None
    sentence_overlap = None
    fixed_size = None

    if strategy == "Hierarchical with Overlap":
        paragraph_overlap = st.sidebar.slider("Paragraph overlap (sentences)", 0, 5, 2)
        sentence_overlap = st.sidebar.slider("Sentence overlap (characters)", 0, 200, 100)
    elif strategy == "Fixed-size":
        fixed_size = st.sidebar.slider("Fixed-size chunk length (words)", 50, 500, 200, step=50)

    if st.sidebar.button("Run Chunking"):
        st.subheader(f"Chunking: {doc_name}")

        # Map strategy to chunker mode
        if strategy == "Hierarchical":
            mode = "hierarchical"
        elif strategy == "Hierarchical with Overlap":
            mode = "hierarchical_overlap"
        else:
            mode = "fixed_size"

        chunker = HierarchicalChunker(
            doc_id=os.path.splitext(doc_name)[0],
            title=doc_name,
            paragraph_overlap_sentences=paragraph_overlap if paragraph_overlap else 0,
            sentence_overlap_chars=sentence_overlap if sentence_overlap else 0,
            strategy=mode,
            fixed_chunk_size=fixed_size if fixed_size else 200
        )

        content = docs[doc_name]
        chunks = chunker.chunk_document(content)

        # Show stats
        st.markdown("### 📊 Chunking Statistics")
        analysis = get_chunking_analysis(chunks)
        st.json(analysis)

        st.markdown("### 🔍 Sample Chunks")
        for c in analysis["sample_retrievable_chunks"]:
            with st.expander(f"Chunk {c['id']} ({c['level']})"):
                st.markdown("**Full Content:**")
                st.write(c["content_preview"])  # now we want full content
                if "core_content" in c["metadata"]:
                    st.markdown("**Core Content:**")
                    st.write(c["metadata"]["core_content"])
                st.markdown("**Metadata:**")
                st.json(c["metadata"])

if __name__ == "__main__":
    main()
