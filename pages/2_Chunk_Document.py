import streamlit as st
import sys
import os
import uuid # For generating unique document IDs if needed

# Add the parent directory of 'pages' to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chunker import (
    HierarchicalChunker,
    get_chunking_analysis,
    Chunk # Import the Chunk dataclass to display its properties
)

st.set_page_config(page_title="Chunk Document", page_icon="✂️")
st.title("✂️ Chunk Your Document")

if "document_structure" not in st.session_state or not st.session_state.document_structure:
    st.warning("Please create a document on the 'Create Document' page first.")
    st.stop()

# Reconstruct the full document text from session state
full_document_text = ""
document_title = "Untitled Document" # Default title
for i, element in enumerate(st.session_state.document_structure):
    if i == 0 and element["type"] == "heading" and element["level"] == 1:
        document_title = element["text"] # Use the first H1 as document title
    
    if element["type"] == "heading":
        full_document_text += f"{'#' * element['level']} {element['text']}\n"
        if element.get("content"):
            full_document_text += f"{element['content']}\n\n"
        for sub_heading in element["sub_headings"]:
            full_document_text += f"{'#' * sub_heading['level']} {sub_heading['text']}\n"
            if sub_heading.get("content"):
                full_document_text += f"{sub_heading['content']}\n\n"

st.subheader("Document to be Chunked:")
st.text_area("Your Document Content", full_document_text, height=200, disabled=True)
st.markdown("---")

st.subheader("Choose Chunking Strategy")
chunking_method = st.radio(
    "Select a chunking method:",
    ("Hierarchical (No Overlap)", "Hierarchical with Overlap"),
    index=1 # Default to Hierarchical with Overlap as it's the main focus of the new class
)

chunks = []
analysis = None

if chunking_method == "Hierarchical (No Overlap)":
    st.markdown("---")
    st.subheader("Hierarchical Chunking Parameters")
    st.info("This option uses the HierarchicalChunker with 0 overlap, focusing on distinct hierarchical levels.")
    
    paragraph_overlap_sentences = 0
    sentence_overlap_chars = 0
    
    if st.button("Execute Hierarchical Chunking"):
        doc_id = str(uuid.uuid4()) # Generate a unique ID for the document
        chunker_instance = HierarchicalChunker(
            doc_id=doc_id, 
            title=document_title,
            paragraph_overlap_sentences=paragraph_overlap_sentences,
            sentence_overlap_chars=sentence_overlap_chars
        )
        with st.spinner("Chunking document..."):
            chunks = chunker_instance.chunk_document(full_document_text)
            analysis = get_chunking_analysis(chunks)
            st.session_state.last_chunks = chunks # Store chunks in session state
            st.session_state.last_chunk_analysis = analysis
            st.session_state.last_chunker_instance = chunker_instance


elif chunking_method == "Hierarchical with Overlap":
    st.markdown("---")
    st.subheader("Hierarchical with Overlap Chunking Parameters")
    paragraph_overlap_sentences = st.number_input(
        "Paragraphs Overlap (sentences)", 
        min_value=0, 
        max_value=10, 
        value=2, 
        help="Number of sentences from previous/next paragraph to include for overlap."
    )
    sentence_overlap_chars = st.number_input(
        "Sentence Overlap (characters)", 
        min_value=0, 
        max_value=200, 
        value=80, 
        step=10,
        help="Number of characters from previous/next sentence to include for overlap."
    )
    if st.button("Execute Hierarchical with Overlap Chunking"):
        doc_id = str(uuid.uuid4()) # Generate a unique ID for the document
        chunker_instance = HierarchicalChunker(
            doc_id=doc_id, 
            title=document_title,
            paragraph_overlap_sentences=paragraph_overlap_sentences,
            sentence_overlap_chars=sentence_overlap_chars
        )
        with st.spinner("Chunking document with overlap..."):
            chunks = chunker_instance.chunk_document(full_document_text)
            analysis = get_chunking_analysis(chunks)
            st.session_state.last_chunks = chunks # Store chunks in session state
            st.session_state.last_chunk_analysis = analysis
            st.session_state.last_chunker_instance = chunker_instance

st.markdown("---")

# Display analysis if available in session state
if "last_chunk_analysis" in st.session_state and st.session_state.last_chunk_analysis:
    analysis = st.session_state.last_chunk_analysis
    chunks = st.session_state.last_chunks
    chunker_instance = st.session_state.last_chunker_instance

    st.subheader("Chunking Analysis")
    st.write(f"**Document Title:** {document_title}")
    st.write(f"**Total Chunks Generated (all levels):** {analysis['total_chunks']}")
    st.write(f"**Total Retrievable Chunks:** {analysis['total_retrievable_chunks']}")
    st.write(f"**Total Characters in Retrievable Chunks:** {analysis['total_characters_retrievable']}")
    st.write(f"**Average Retrievable Chunk Length:** {analysis['avg_chunk_length_retrievable']:.2f} characters")

    st.markdown("---")
    st.subheader("Chunk Counts by Level")
    level_df = st.dataframe(analysis['chunk_counts_by_level'], use_container_width=True)
    
    st.markdown("---")
    st.subheader("Overlap Statistics (for Hierarchical with Overlap)")
    if chunker_instance:
        overlap_stats = chunker_instance.get_overlapping_stats()
        st.write(f"**Chunks with Overlap:** {overlap_stats['chunks_with_overlap']}")
        st.write(f"**Paragraph Overlaps:** {overlap_stats['paragraph_overlaps']}")
        st.write(f"**Sentence Overlaps:** {overlap_stats['sentence_overlaps']}")
        if overlap_stats['overlap_types']:
            st.write("**Overlap Types:**")
            st.json(overlap_stats['overlap_types'])
        else:
            st.info("No explicit overlap types detected, possibly due to 'Hierarchical (No Overlap)' selection or no suitable content for overlap.")


    st.markdown("---")
    st.subheader("Sample Retrievable Chunks:")
    if analysis['sample_retrievable_chunks']:
        for i, sample_chunk_data in enumerate(analysis['sample_retrievable_chunks']):
            st.write(f"**Chunk {i+1} (Level: {sample_chunk_data['level']})**")
            st.write(f"ID: `{sample_chunk_data['id']}`")
            st.code(sample_chunk_data['content_preview'], language="text")
            with st.expander("View Full Metadata"):
                st.json(sample_chunk_data['metadata'])
            st.markdown("---")
    else:
        st.info("No retrievable chunks generated. Adjust your document or chunking parameters.")

    st.subheader("Visualize Document Hierarchy")
    st.info("This will show the full chunk structure including non-retrievable chunks.")
    if st.button("Show Full Chunk Tree"):
        # Display the full chunk list for inspection
        st.dataframe([c.__dict__ for c in chunks], use_container_width=True)

        # Example of how you might visualize or inspect the tree
        st.markdown("#### Document Root Chunk")
        doc_chunk = next((c for c in chunks if c.level == 'document'), None)
        if doc_chunk:
            st.json(doc_chunk.__dict__)
            st.markdown("##### First Section Child")
            if doc_chunk.children_ids:
                first_section = chunker_instance.chunk_lookup.get(doc_chunk.children_ids[0])
                if first_section:
                    st.json(first_section.__dict__)
                    st.markdown("###### First Paragraph Child of Section")
                    if first_section.children_ids:
                        first_paragraph = chunker_instance.chunk_lookup.get(first_section.children_ids[0])
                        if first_paragraph:
                            st.json(first_paragraph.__dict__)
                            st.markdown("####### First Sentence Child of Paragraph")
                            if first_paragraph.children_ids:
                                first_sentence = chunker_instance.chunk_lookup.get(first_paragraph.children_ids[0])
                                if first_sentence:
                                    st.json(first_sentence.__dict__)
                                else:
                                    st.write("No sentence children for this paragraph.")
                            else:
                                st.write("No paragraph children for this section.")
                        else:
                            st.write("No paragraph children for this section.")
                    else:
                        st.write("No section children for this document.")
                else:
                    st.write("No section children for this document.")
            else:
                st.write("No children for the document chunk.")
        else:
            st.error("Document root chunk not found.")