import streamlit as st
import json
from datetime import datetime

st.set_page_config(
    page_title="RAG Document Creator & Chunker",
    page_icon="📄",
    layout="wide"
)

# Initialize session state for cross-page data sharing
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'current_doc_id' not in st.session_state:
    st.session_state.current_doc_id = None

st.sidebar.header("🔄 RAG Workflow")
st.sidebar.success("Select a page above to get started.")

# Show current session statistics in sidebar
if st.session_state.documents:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Session Summary")
    st.sidebar.metric("Documents Created", len(st.session_state.documents))
    
    total_sections = sum(len(doc.get('sections', [])) for doc in st.session_state.documents.values())
    st.sidebar.metric("Total Sections", total_sections)
    
    if st.sidebar.button("🗑️ Clear All Documents"):
        st.session_state.documents = {}
        st.session_state.current_doc_id = None
        st.sidebar.success("All documents cleared!")
        st.rerun()

# Main content
st.write("# Welcome to the RAG Document Creator! 👋")

st.markdown(
    """
    This application provides a complete workflow for creating and processing documents for your **RAG (Retrieval Augmented Generation)** system. 
    Build structured, hierarchical documents that optimize for intelligent chunking and superior retrieval performance.
    """
)

# Workflow overview
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## 🔄 Complete RAG Workflow
    
    ### **Step 1: Create Document** 📝
    - Design documents with proper hierarchical structure
    - Use templates for common document types (handbooks, manuals, policies)
    - Add sections, subsections, paragraphs, and sentences
    - Real-time preview with chunking analysis
    
    ### **Step 2: Chunk Document** ⚡
    - Process your document using advanced hierarchical chunking
    - Generate multi-level chunks (document → section → paragraph → sentence)
    - Add contextual information to improve embedding quality
    - Export chunks for vector database ingestion
    
    ### **Step 3: Embed & Retrieve** 🔍
    - Import chunks into your vector database
    - Create embeddings for retrievable chunks
    - Query with intelligent context-aware retrieval
    - Get precise answers with appropriate context levels
    """)

with col2:
    st.markdown("### 🎯 Why Use This System?")
    
    st.info("""
    **Better Retrieval Quality**
    - Hierarchical context improves embedding accuracy
    - Smart chunking prevents information loss
    - Adaptive retrieval returns optimal context levels
    """)
    
    st.success("""
    **Consistent Structure** 
    - Templates ensure document consistency
    - Proper formatting for chunking algorithms
    - Standardized metadata and organization
    """)
    
    st.warning("""
    **Production Ready**
    - Export to multiple formats
    - Integrates with existing RAG pipelines
    - Scalable for large document collections
    """)

# Getting started section
st.markdown("---")
st.markdown("## 🚀 Getting Started")

# Quick action buttons
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📝 New to Document Creation?
    Start with our guided document creator using pre-built templates.
    """)
    if st.button("🆕 Create Your First Document", type="primary"):
        st.switch_page("pages/1_📝_Create_Document.py")

with col2:
    st.markdown("""
    ### ⚡ Ready to Process Documents?
    Already have documents? Jump straight to the chunking workflow.
    """)
    if st.button("⚡ Start Chunking Process"):
        st.switch_page("pages/2_⚡_Chunk_Document.py")

with col3:
    st.markdown("""
    ### 📚 Learn More
    Understand how hierarchical chunking improves RAG performance.
    """)
    if st.button("📖 View Documentation"):
        st.info("Documentation page coming soon!")

# Show recent documents if any exist
if st.session_state.documents:
    st.markdown("---")
    st.markdown("## 📚 Recent Documents")
    
    # Sort documents by last modified
    sorted_docs = sorted(
        st.session_state.documents.items(), 
        key=lambda x: x[1].get('last_modified', ''), 
        reverse=True
    )
    
    for doc_id, doc in sorted_docs[:5]:  # Show latest 5
        with st.expander(f"📄 {doc.get('title', 'Untitled Document')} ({doc_id})"):
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                st.markdown(f"**Created:** {doc.get('created_at', 'Unknown')[:19]}")
                st.markdown(f"**Last Modified:** {doc.get('last_modified', 'Unknown')[:19]}")
                st.markdown(f"**Sections:** {len(doc.get('sections', []))}")
                
                # Show intro preview
                intro = doc.get('intro', '')
                if intro:
                    preview = intro[:150] + "..." if len(intro) > 150 else intro
                    st.markdown(f"**Preview:** {preview}")
            
            with col_actions:
                if st.button(f"✏️ Edit", key=f"edit_{doc_id}"):
                    st.session_state.current_doc_id = doc_id
                    st.switch_page("pages/1_📝_Create_Document.py")
                
                if st.button(f"⚡ Chunk", key=f"chunk_{doc_id}"):
                    st.session_state.current_doc_id = doc_id
                    st.switch_page("pages/2_⚡_Chunk_Document.py")

# Features overview
st.markdown("---")
st.markdown("## ✨ Key Features")

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown("""
    ### 🏗️ **Structured Creation**
    - **Template Library**: Pre-built templates for common document types
    - **Hierarchical Organization**: Proper heading structure for optimal chunking
    - **Real-time Preview**: See your document formatted as you build
    - **Consistency Enforcement**: Maintains proper structure across all documents
    """)

with feature_col2:
    st.markdown("""
    ### ⚙️ **Advanced Chunking**
    - **Multi-level Hierarchy**: Document → Section → Paragraph → Sentence
    - **Contextual Enhancement**: Adds parent context to improve embeddings
    - **Smart Retrieval**: Returns appropriate context level based on query type
    - **Metadata Enrichment**: Tracks relationships and chunk properties
    """)

with feature_col3:
    st.markdown("""
    ### 🔍 **RAG Optimization**
    - **Retrievable Chunks**: Only embeds chunks suitable for retrieval
    - **Context Preservation**: Maintains document structure and relationships
    - **Adaptive Responses**: Returns precise facts or broad context as needed
    - **Export Ready**: Direct integration with vector databases
    """)

# Technical specifications
with st.expander("🔧 Technical Specifications"):
    st.markdown("""
    ### 📋 Supported Document Types
    - Employee Handbooks and HR Policies
    - Technical Documentation and API Guides
    - Standard Operating Procedures (SOPs)
    - Training Manuals and Educational Content
    - Compliance and Regulatory Documents
    
    ### ⚡ Chunking Specifications
    - **Document Level**: Complete document (1 chunk)
    - **Section Level**: Major headings (non-retrievable, structural)
    - **Paragraph Level**: 50-200 words (primary retrieval target)
    - **Sentence Level**: Individual facts (precise retrieval target)
    
    ### 🔗 Export Formats
    - Markdown (.md files)
    - JSON (structured data with metadata)
    - Plain text (for direct copy-paste)
    - Chunked output (ready for vector DB)
    
    ### 🎯 Embedding Optimization
    - Contextual content enhancement
    - Parent-child relationship tracking
    - Retrievability flags for selective embedding
    - Metadata preservation for filtering and routing
    """)

# Footer with tips
st.markdown("---")
st.markdown("""
### 💡 **Pro Tips for Better RAG Performance**

1. **Write Complete Thoughts**: Each paragraph should contain a complete idea that can stand alone
2. **Use Descriptive Headings**: Section titles become context for all child chunks
3. **Include Specific Details**: Facts, numbers, and procedures work best for retrieval
4. **Maintain Logical Flow**: Related information should be grouped in the same section
5. **Test Your Content**: Use the chunking preview to see how your document will be processed

**👈 Ready to start? Use the sidebar to navigate to Create Document or Chunk Document!**
""")