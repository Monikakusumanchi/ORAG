# pages/3_Embeddings.py
import os
import sys
import json
import uuid
import faiss
import numpy as np
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Add parent directory to import chunker if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

# Make sure the API key is available
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY not found in .env. Please set it.")
    st.stop()
else:
    client = OpenAI(api_key=api_key)

# Paths
DATA_DIR = "processed_docs"   # where chunked docs are stored
INDEX_DIR = "vector_store"    # where FAISS indexes will be stored
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

st.title("🔹 Create Embeddings for Documents")

# Step 1: Select a processed document
docs = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
if not docs:
    st.warning("⚠️ No processed documents found. Please go to '2_Chunk_Document' and chunk files first.")
    st.stop()

doc_file = st.selectbox("📑 Select a document", docs)

with open(os.path.join(DATA_DIR, doc_file), "r", encoding="utf-8") as f:
    doc_data = json.load(f)

chunks = doc_data.get("chunks", [])
if not chunks:
    st.error("❌ No chunks found in this document. Please check chunking step.")
    st.stop()

st.success(f"Loaded `{doc_file}` with {len(chunks)} chunks")

# Step 2: Choose embedding model
embedding_model = st.selectbox(
    "🤖 Select embedding model",
    ["text-embedding-3-small", "text-embedding-3-large"]
)

# Step 3: Generate embeddings
if st.button("🚀 Generate & Save Embeddings"):
    embeddings = []
    metadata = []

    st.info("Generating embeddings... this may take a while ⏳")

    for idx, chunk in enumerate(chunks):
        try:
            response = client.embeddings.create(
                model=embedding_model,
                input=chunk["content"]
            )
            vector = response.data[0].embedding
            embeddings.append(vector)

            metadata.append({
                "doc_id": doc_data["doc_id"],
                "doc_name": doc_data.get("doc_name", ""),
                "chunk_id": chunk["id"],
                "strategy": doc_data.get("strategy", "unknown"),
                "embedding_model": embedding_model,
                "content": chunk["content"],
                "level": chunk.get("level", ""),
                "metadata": chunk.get("metadata", {})
            })

        except Exception as e:
            st.error(f"Error generating embedding for chunk {idx}: {e}")
            st.stop()

    # Convert to numpy array for FAISS
    embeddings_np = np.array(embeddings).astype("float32")

    # Create FAISS index
    dim = len(embeddings_np[0])
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_np)

    # Save FAISS index
    index_path = os.path.join(INDEX_DIR, f"{doc_data['doc_id']}_index.faiss")
    faiss.write_index(index, index_path)

    # Save metadata
    meta_path = os.path.join(INDEX_DIR, f"{doc_data['doc_id']}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    st.success(f"✅ Saved embeddings & metadata for {len(chunks)} chunks")
    st.write(f"**FAISS index:** `{index_path}`")
    st.write(f"**Metadata file:** `{meta_path}`")

    st.markdown("### 🔍 Example Metadata Entry")
    st.json(metadata[0])  # show preview
