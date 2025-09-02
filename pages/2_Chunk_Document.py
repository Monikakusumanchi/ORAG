# pages/2_Chunk_Document.py
import os
import json
import streamlit as st
from chunking import HierarchicalChunker, get_chunking_analysis

DATA_DIR = "data"
PROCESSED_DIR = "processed_docs"
os.makedirs(PROCESSED_DIR, exist_ok=True)

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

def chunk_to_dict(chunk):
    """Convert Chunk object to JSON serializable dict."""
    return {
        "id": chunk.id,
        "content": chunk.content,
        "level": chunk.level,
        "parent_id": chunk.parent_id,
        "children_ids": chunk.children_ids,
        "metadata": chunk.metadata,
    }

def save_chunks(doc_id, doc_name, strategy, chunks):
    """Save chunks and metadata to JSON for later embedding."""
    out = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "strategy": strategy,
        "chunks": [chunk_to_dict(c) for c in chunks],
    }
    out_path = os.path.join(PROCESSED_DIR, f"{doc_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

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

    # ---- Preview single document ----
    if st.sidebar.button("Run Chunking"):
        st.subheader(f"Chunking Preview: {doc_name}")

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
                st.write(c["content_preview"])
                if "core_content" in c["metadata"]:
                    st.markdown("**Core Content:**")
                    st.write(c["metadata"]["core_content"])
                st.markdown("**Metadata:**")
                st.json(c["metadata"])

    # ---- Process all documents and save ----
    if st.sidebar.button("🚀 Create Chunks for All Documents"):
        st.subheader("Processing all documents...")

        for fname, content in docs.items():
            doc_id = os.path.splitext(fname)[0]

            # Map strategy
            if strategy == "Hierarchical":
                mode = "hierarchical"
            elif strategy == "Hierarchical with Overlap":
                mode = "hierarchical_overlap"
            else:
                mode = "fixed_size"

            chunker = HierarchicalChunker(
                doc_id=doc_id,
                title=fname,
                paragraph_overlap_sentences=paragraph_overlap if paragraph_overlap else 0,
                sentence_overlap_chars=sentence_overlap if sentence_overlap else 0,
                strategy=mode,
                fixed_chunk_size=fixed_size if fixed_size else 200
            )

            chunks = chunker.chunk_document(content)

            # Save to processed_docs
            save_chunks(doc_id, fname, mode, chunks)

        st.success(f"✅ All documents processed and saved in `{PROCESSED_DIR}`")

if __name__ == "__main__":
    main()
