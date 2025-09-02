import streamlit as st
import uuid
from datetime import datetime
import json
import re

# Initialize session state (these are critical for the app to remember user's documents)
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'current_doc_id' not in st.session_state:
    st.session_state.current_doc_id = None
if 'sections' not in st.session_state: # This will hold the sections for the currently active document
    st.session_state.sections = []

def generate_doc_id():
    # Your existing logic for current_doc_id
    if 'current_doc_id' not in st.session_state:
        st.session_state.current_doc_id = generate_unique_id("doc")
    return st.session_state.current_doc_id

def generate_unique_id(prefix=""):
    """Generates a short unique ID."""
    return f"{prefix}_{str(uuid.uuid4())[:8]}"

def create_new_document():
    """Initialize a new document structure and set it as current"""
    doc_id = generate_doc_id()
    st.session_state.current_doc_id = doc_id
    st.session_state.sections = [] # Reset sections for the new document
    
    # Initialize document in session state
    st.session_state.documents[doc_id] = {
        'id': doc_id,
        'title': '',
        'intro': '',
        'sections': [],
        'created_at': datetime.now().isoformat(),
        'last_modified': datetime.now().isoformat()
    }
    
    return doc_id

def add_section():
    doc_id = st.session_state.current_doc_id
    current_doc_sections = st.session_state.documents[doc_id].get('sections', [])
    
    section_id = generate_unique_id(f"section_{len(current_doc_sections) + 1}")
    new_section = {
        'id': section_id,
        'title': f'New Section {len(current_doc_sections) + 1}',
        'level': 1,  # Default to h1
        'paragraphs': [], # <--- ADDED: Initialize empty paragraphs list
        'subsections': []
    }
    current_doc_sections.append(new_section)
    st.session_state.documents[doc_id]['sections'] = current_doc_sections # Update session state
    st.rerun() # Rerun to display the new section immediately

def add_subsection(parent_section_index: int):
    doc_id = st.session_state.current_doc_id
    current_doc_sections = st.session_state.documents[doc_id].get('sections', [])
    
    if parent_section_index < len(current_doc_sections):
        parent_section = current_doc_sections[parent_section_index]
        parent_level = parent_section.get('level', 1)
        
        subsection_id = generate_unique_id(f"section_{parent_section_index + 1}.{len(parent_section['subsections']) + 1}")
        new_subsection = {
            'id': subsection_id,
            'title': f'New Subsection {len(parent_section['subsections']) + 1}',
            'level': parent_level + 1,
            'paragraphs': [], # <--- ADDED: Initialize empty paragraphs list
            'subsections': []
        }
        parent_section['subsections'].append(new_subsection)
        st.session_state.documents[doc_id]['sections'] = current_doc_sections # Update session state
        st.rerun()

def find_section_by_id(sections_list, target_id):
    """Recursively finds a section/subsection by its ID."""
    for s in sections_list:
        if s['id'] == target_id:
            return s
        if s.get('subsections'):
            found = find_section_by_id(s['subsections'], target_id)
            if found:
                return found
    return None

def add_paragraph(parent_section_id: str):
    doc_id = st.session_state.current_doc_id
    current_doc_sections = st.session_state.documents[doc_id].get('sections', [])
    
    target_section = find_section_by_id(current_doc_sections, parent_section_id)

    if target_section:
        # Ensure 'paragraphs' key exists
        if 'paragraphs' not in target_section:
            target_section['paragraphs'] = []

        paragraph_order = len(target_section['paragraphs']) + 1
        paragraph_id = generate_unique_id(f"para_{target_section['id'].split('_')[1]}_{paragraph_order}") # e.g., para_1_1_abc12345
        new_paragraph = {
            'id': paragraph_id,
            'content': '', # Start with empty content
            'order': paragraph_order
        }
        target_section['paragraphs'].append(new_paragraph)
        st.session_state.documents[doc_id]['sections'] = current_doc_sections # Update session state
        st.rerun()
    else:
        st.error(f"Error: Target section with ID '{parent_section_id}' not found to add paragraph.")

def remove_paragraph(parent_section_id: str, paragraph_id_to_remove: str):
    doc_id = st.session_state.current_doc_id
    current_doc_sections = st.session_state.documents[doc_id].get('sections', [])
    
    target_section = find_section_by_id(current_doc_sections, parent_section_id)

    if target_section and 'paragraphs' in target_section:
        initial_len = len(target_section['paragraphs'])
        target_section['paragraphs'] = [
            p for p in target_section['paragraphs'] if p['id'] != paragraph_id_to_remove
        ]
        if len(target_section['paragraphs']) < initial_len:
            # Re-order remaining paragraphs
            for i, p in enumerate(target_section['paragraphs']):
                p['order'] = i + 1
            st.session_state.documents[doc_id]['sections'] = current_doc_sections # Update session state
            st.rerun()
        else:
            st.warning("Paragraph not found to remove.")
    else:
        st.error(f"Error: Target section with ID '{parent_section_id}' not found or has no paragraphs.")


# Placeholder for your markdown generation logic
def generate_markdown_document(doc):
    markdown_output = []
    
    if doc.get('title'):
        markdown_output.append(f"# {doc['title']}\n")
    if doc.get('intro'):
        markdown_output.append(f"{doc['intro']}\n")

    def render_section_to_markdown(section_data):
        md_part = []
        level_hashes = '#' * section_data.get('level', 1)
        md_part.append(f"{level_hashes} {section_data.get('title', 'Untitled Section')}\n")
        
        # Render paragraphs
        for para in section_data.get('paragraphs', []):
            if para.get('content'):
                md_part.append(f"{para['content']}\n") # Paragraphs are just content + newline
        
        # Render subsections recursively
        for sub in section_data.get('subsections', []):
            md_part.extend(render_section_to_markdown(sub))
        
        return md_part

    for section in doc.get('sections', []):
        markdown_output.extend(render_section_to_markdown(section))
        
    return "\n".join(markdown_output)

def save_document():
    """Save current document's structure and metadata to session state"""
    if st.session_state.current_doc_id:
        doc_id = st.session_state.current_doc_id
        st.session_state.documents[doc_id]['sections'] = st.session_state.sections
        st.session_state.documents[doc_id]['last_modified'] = datetime.now().isoformat()
        # The title and intro are updated directly in the input widgets,
        # so they are already in st.session_state.documents[doc_id]

# Document templates
def load_template(template_type):
    """Load predefined templates and apply to a new document"""
    templates = {
        "employee_handbook": {
            "title": "Employee Handbook",
            "intro": "Welcome to our organization! This handbook serves as your comprehensive guide to company policies, procedures, benefits, and workplace expectations. Please read through this document carefully and refer to it whenever you have questions about your employment.",
            "sections": [
                {
                    "id": f"section_1_{generate_doc_id()}",
                    "title": "Company Overview",
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_1_{generate_doc_id()}", "title": "Mission and Values", "level": 2, "content": "Our mission is to [insert mission statement]. We are guided by core values of integrity, innovation, collaboration, and customer focus."},
                        {"id": f"subsection_2_{generate_doc_id()}", "title": "Company History", "level": 2, "content": "Founded in [year], our company has grown from [origin story] to become [current status]."}
                    ]
                },
                {
                    "id": f"section_2_{generate_doc_id()}",
                    "title": "Employment Policies", 
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_3_{generate_doc_id()}", "title": "Equal Opportunity Employment", "level": 2, "content": "We are an equal opportunity employer committed to creating an inclusive workplace for all employees."},
                        {"id": f"subsection_4_{generate_doc_id()}", "title": "At-Will Employment", "level": 2, "content": "Employment is at-will, meaning either party may terminate the relationship at any time."}
                    ]
                },
                {
                    "id": f"section_3_{generate_doc_id()}",
                    "title": "Work Hours and Attendance",
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_5_{generate_doc_id()}", "title": "Standard Work Schedule", "level": 2, "content": "Standard business hours are 9:00 AM to 5:00 PM, Monday through Friday."},
                        {"id": f"subsection_6_{generate_doc_id()}", "title": "Remote Work Policy", "level": 2, "content": "Remote work is available [specify conditions and requirements]."}
                    ]
                }
            ]
        },
        "technical_manual": {
            "title": "Technical Documentation",
            "intro": "This technical manual provides comprehensive guidance for system implementation, configuration, and maintenance. It is designed for technical professionals and system administrators.",
            "sections": [
                {
                    "id": f"section_1_{generate_doc_id()}",
                    "title": "Getting Started",
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_1_{generate_doc_id()}", "title": "Prerequisites", "level": 2, "content": "Before beginning installation, ensure your system meets the following requirements: [list requirements]."},
                        {"id": f"subsection_2_{generate_doc_id()}", "title": "System Overview", "level": 2, "content": "This system provides [describe functionality and purpose]."}
                    ]
                },
                {
                    "id": f"section_2_{generate_doc_id()}",
                    "title": "Installation Guide",
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_3_{generate_doc_id()}", "title": "Download and Setup", "level": 2, "content": "Download the installation package from [source] and follow these steps: [detailed steps]."},
                        {"id": f"subsection_4_{generate_doc_id()}", "title": "Initial Configuration", "level": 2, "content": "Configure the system using the following parameters: [configuration details]."}
                    ]
                }
            ]
        },
        "policy_document": {
            "title": "Company Policies and Procedures",
            "intro": "This document outlines important company policies and procedures that all employees must understand and follow. These policies ensure a safe, productive, and compliant work environment.",
            "sections": [
                {
                    "id": f"section_1_{generate_doc_id()}",
                    "title": "Code of Conduct",
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_1_{generate_doc_id()}", "title": "Professional Behavior", "level": 2, "content": "All employees are expected to maintain professional conduct in all business interactions."},
                        {"id": f"subsection_2_{generate_doc_id()}", "title": "Anti-Harassment Policy", "level": 2, "content": "We maintain a zero-tolerance policy for harassment of any kind."}
                    ]
                },
                {
                    "id": f"section_2_{generate_doc_id()}",
                    "title": "Workplace Safety",
                    "level": 1,
                    "subsections": [
                        {"id": f"subsection_3_{generate_doc_id()}", "title": "General Safety Guidelines", "level": 2, "content": "All employees must follow established safety procedures to maintain a safe work environment."},
                        {"id": f"subsection_4_{generate_doc_id()}", "title": "Emergency Procedures", "level": 2, "content": "In case of emergency, follow these established procedures: [emergency steps]."}
                    ]
                }
            ]
        }
    }
    
    return templates.get(template_type, {})

# Help section
def show_help():
    """Show help and best practices"""
    with st.expander("❓ Help & Best Practices"):
        st.markdown("""
        ### 📋 Document Structure Best Practices:
        
        **1. Clear Hierarchy**
        - Use logical heading levels (H1 for main sections, H2 for subsections, etc.)
        - Keep section titles concise and descriptive
        - Maintain consistent formatting throughout
        
        **2. Content Guidelines**
        - Write clear, complete paragraphs (50-200 words ideal for retrievable chunks)
        - Use specific, factual language
        - Include relevant details and context
        - Break up long content into distinct subsections
        
        **3. Benefits for Chunking**
        - Each subsection should ideally cover one complete topic or a logical sub-topic.
        - Avoid splitting closely related information across different subsections.
        - Ensure each piece of content has enough context to be understood if retrieved independently.
        - Descriptive headings help the chunker (and ultimately the RAG system) understand the content's purpose.
        
        **4. Example of Good Section Content**:
        ```markdown
        ## Vacation Policy
        
        Full-time employees accrue vacation time based on their length of service. 
        New employees (0-2 years) earn 2.5 days per month, totaling 20 days annually.
        
        Vacation requests must be submitted at least two weeks in advance through 
        the HR portal. Manager approval is required, and requests are subject to 
        business needs and adequate coverage requirements.
        ```
        
        **5. Content That Works Well for RAG**:
        - Policy explanations with specific details
        - Step-by-step procedures or instructions
        - Requirements, specifications, and definitions
        - Examples and use cases
        - FAQs and their answers
        """)

def find_section_by_id(sections_list, target_id):
    """Recursively finds a section/subsection by its ID."""
    for s in sections_list:
        if s['id'] == target_id:
            return s
        if s.get('subsections'):
            found = find_section_by_id(s['subsections'], target_id)
            if found:
                return found
    return None

def add_paragraph(parent_section_id: str):
    doc_id = st.session_state.current_doc_id
    current_doc_sections = st.session_state.documents[doc_id].get('sections', [])
    
    target_section = find_section_by_id(current_doc_sections, parent_section_id)

    if target_section:
        # Ensure 'paragraphs' key exists
        if 'paragraphs' not in target_section:
            target_section['paragraphs'] = []

        paragraph_order = len(target_section['paragraphs']) + 1
        paragraph_id = generate_unique_id(f"para_{target_section['id'].split('_')[1]}_{paragraph_order}") # e.g., para_1_1_abc12345
        new_paragraph = {
            'id': paragraph_id,
            'content': '', # Start with empty content
            'order': paragraph_order
        }
        target_section['paragraphs'].append(new_paragraph)
        st.session_state.documents[doc_id]['sections'] = current_doc_sections # Update session state
        st.rerun()
    else:
        st.error(f"Error: Target section with ID '{parent_section_id}' not found to add paragraph.")

def remove_paragraph(parent_section_id: str, paragraph_id_to_remove: str):
    doc_id = st.session_state.current_doc_id
    current_doc_sections = st.session_state.documents[doc_id].get('sections', [])
    
    target_section = find_section_by_id(current_doc_sections, parent_section_id)

    if target_section and 'paragraphs' in target_section:
        initial_len = len(target_section['paragraphs'])
        target_section['paragraphs'] = [
            p for p in target_section['paragraphs'] if p['id'] != paragraph_id_to_remove
        ]
        if len(target_section['paragraphs']) < initial_len:
            # Re-order remaining paragraphs
            for i, p in enumerate(target_section['paragraphs']):
                p['order'] = i + 1
            st.session_state.documents[doc_id]['sections'] = current_doc_sections # Update session state
            st.rerun()
        else:
            st.warning("Paragraph not found to remove.")
    else:
        st.error(f"Error: Target section with ID '{parent_section_id}' not found or has no paragraphs.")


# Placeholder for your markdown generation logic
def generate_markdown_document(doc):
    markdown_output = []
    
    if doc.get('title'):
        markdown_output.append(f"# {doc['title']}\n")
    if doc.get('intro'):
        markdown_output.append(f"{doc['intro']}\n")

    def render_section_to_markdown(section_data):
        md_part = []
        level_hashes = '#' * section_data.get('level', 1)
        md_part.append(f"{level_hashes} {section_data.get('title', 'Untitled Section')}\n")
        
        # Render paragraphs
        for para in section_data.get('paragraphs', []):
            if para.get('content'):
                md_part.append(f"{para['content']}\n") # Paragraphs are just content + newline
        
        # Render subsections recursively
        for sub in section_data.get('subsections', []):
            md_part.extend(render_section_to_markdown(sub))
        
        return md_part

    for section in doc.get('sections', []):
        markdown_output.extend(render_section_to_markdown(section))
        
    return "\n".join(markdown_output)


def show_help():
    st.sidebar.markdown("""
        ### Help
        - **Document Editor**: Add and manage sections, subsections, and paragraphs.
        - **Live Preview**: See your document rendered in Markdown.
        - **Export Options**: Download as Markdown or copy the formatted text.
    """)

# --- Main Streamlit App Page 1 ---
def app_page_1():
    # Ensure session_state has necessary initializations
    if 'current_doc_id' not in st.session_state:
        st.session_state.current_doc_id = generate_unique_id("doc")
    if 'documents' not in st.session_state:
        st.session_state.documents = {}
    if st.session_state.current_doc_id not in st.session_state.documents:
        st.session_state.documents[st.session_state.current_doc_id] = {
            'id': st.session_state.current_doc_id,
            'title': 'New Document',
            'intro': '',
            'sections': []
        }

    current_doc = st.session_state.documents[st.session_state.current_doc_id]
    
    st.header(f"✏️ Editing: {current_doc.get('title', 'Untitled Document')}")
    
    # Two column layout for editor and preview
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Document Editor")
        
        # Document title and intro
        with st.container():
            st.markdown("### 📄 Document Header")
            
            title = st.text_input(
                "Document Title",
                value=current_doc.get('title', ''),
                placeholder="Enter document title...",
                key=f"doc_title_{st.session_state.current_doc_id}" # Unique key for current doc
            )
            
            intro = st.text_area(
                "Introduction",
                value=current_doc.get('intro', ''),
                placeholder="Write an introduction that explains the purpose and scope of this document...",
                height=100,
                key=f"doc_intro_{st.session_state.current_doc_id}" # Unique key
            )
            
            # Update document state (important for persistence)
            current_doc['title'] = title
            current_doc['intro'] = intro
        
        # Sections management
        st.markdown("### 📚 Sections")
        
        if st.button("➕ Add New Top-Level Section"):
            add_section() # This now operates on current_doc['sections']
        
        # --- RECURSIVE RENDERING OF SECTIONS AND PARAGRAPHS ---
        def render_section_editor_recursive(sections_list, parent_key_prefix=""):
            for i, section in enumerate(sections_list):
                section_key_prefix = f"{parent_key_prefix}_section_{section['id']}_{i}"
                with st.expander(
                    f"{'📋' if section.get('level', 1) == 1 else '📂'} Section {i+1}: {section.get('title', 'Untitled Section')}",
                    # REMOVE THIS LINE: key=f"exp_{section_key_prefix}"
                    expanded=True
                ):
                    
                    col_title, col_level = st.columns([3, 1])
                    with col_title:
                        section_title = st.text_input(
                            "Section Title",
                            value=section.get('title', ''),
                            placeholder="Enter section title...",
                            key=f"title_{section_key_prefix}"
                        )
                        section['title'] = section_title
                    
                    with col_level:
                        section_level = st.selectbox(
                            "Heading Level",
                            options=[1, 2, 3, 4],
                            index=min(section.get('level', 1) - 1, 3),
                            key=f"level_{section_key_prefix}"
                        )
                        section['level'] = section_level
                    
                    st.markdown("---")
                    st.markdown(f"**Paragraphs in '{section.get('title', 'Untitled')}'**")
                    
                    # --- Paragraphs for THIS section/subsection ---
                    if 'paragraphs' not in section:
                        section['paragraphs'] = [] # Ensure it exists

                    for p_idx, paragraph in enumerate(section['paragraphs']):
                        col_para_content, col_para_remove = st.columns([6, 1])
                        with col_para_content:
                            paragraph['content'] = st.text_area(
                                f"Paragraph {paragraph['order']}",
                                value=paragraph.get('content', ''),
                                placeholder="Write content for this paragraph...",
                                height=70,
                                key=f"para_content_{section_key_prefix}_{paragraph['id']}_{p_idx}"
                            )
                        with col_para_remove:
                            st.write("") # Spacer
                            st.write("") # Spacer
                            if st.button("🗑️", key=f"remove_para_{section_key_prefix}_{paragraph['id']}_{p_idx}", help="Remove this paragraph"):
                                remove_paragraph(section['id'], paragraph['id'])
                    
                    if st.button(f"➕ Add Paragraph to '{section.get('title', 'Untitled')}'", key=f"add_para_{section_key_prefix}"):
                        add_paragraph(section['id']) # Use the section's actual ID
                    
                    st.markdown("---")
                    st.markdown(f"**Subsections of '{section.get('title', 'Untitled')}'**")
                    
                    # Add Subsection button
                    if st.button(f"➕ Add Subsection to '{section.get('title', 'Untitled')}'", key=f"add_sub_{section_key_prefix}"):
                        # Find the index of this section in its parent list to pass to add_subsection
                        # This part needs adjustment as add_subsection expects an index, but we're in a recursive call
                        # A better approach would be to pass the parent_section_obj or its id.
                        
                        # Simplest for now: ensure 'subsections' list is updated directly
                        parent_level = section.get('level', 1)
                        subsection_id = generate_unique_id(f"section_{section['id'].split('_')[1]}.{len(section['subsections']) + 1}")
                        new_subsection = {
                            'id': subsection_id,
                            'title': f'New Subsection {len(section['subsections']) + 1}',
                            'level': parent_level + 1,
                            'paragraphs': [],
                            'subsections': []
                        }
                        section['subsections'].append(new_subsection)
                        st.rerun() # Rerun to display the new subsection immediately
                    
                    # Recursively render subsections
                    if section.get('subsections'):
                        render_section_editor_recursive(section['subsections'], parent_key_prefix=section_key_prefix) # Pass current section's key as prefix

                    # Remove section button
                    st.markdown("---")
                    if st.button(f"🗑️ Remove Section '{section.get('title', 'Untitled')}'", key=f"remove_section_{section_key_prefix}"):
                        # Find index of this section within its parent list to remove it
                        # This requires knowing the parent list and the index, which is complex in recursive calls.
                        # For simplicity, we'll assume sections_list is the top-level current_doc['sections']
                        # A more robust solution involves passing the parent list down or using a flat lookup for removal.
                        
                        # For now, let's make a simplified removal for top-level sections for demonstration
                        # A full solution would adapt find_section_by_id or pass parent references
                        
                        # Simplified removal for top-level. You need more robust logic for nested removal.
                        if parent_key_prefix == "": # It's a top-level section
                            st.session_state.documents[st.session_state.current_doc_id]['sections'].pop(i)
                        else:
                            # This is where a more complex recursive removal would go
                            # For a quick fix, if you delete a nested section, it will likely just delete the top-level one
                            # or you'd need to re-implement `remove_section` to take section_id and find/remove it
                            st.warning("Removing nested sections directly from this button is not fully implemented yet.")
                            # Example of how you would *find* it to remove:
                            # doc_sections = st.session_state.documents[st.session_state.current_doc_id]['sections']
                            # # Implement a recursive removal function here
                        st.rerun()
                        
        # Call the recursive rendering function for the top-level sections
        if current_doc.get('sections'):
            render_section_editor_recursive(current_doc['sections'])
        else:
            st.info("👆 Add a new top-level section to start building your document structure.")
        
    with col2:
        st.subheader("👁️ Live Preview")
        
        # Generate and show preview
        markdown_content = generate_markdown_document(current_doc)
        
        # Show formatted preview
        if markdown_content.strip():
            st.markdown("#### 📖 Document Preview:")
            st.markdown(markdown_content)
        else:
            st.info("👆 Start adding content on the left to see your document preview here!")
        
        # Export options
        st.markdown("---")
        st.subheader("💾 Export Options")
        
        if markdown_content.strip():
            # Auto-save happens on every interaction, but an explicit button might be nice.
            if st.button("💾 Explicitly Save Document", help="This document is auto-saved on every interaction, but you can explicitly save it too."):
                save_document()
                st.success(f"✅ Document '{current_doc.get('title', 'Untitled')}' saved!")
            
            # Download as markdown
            st.download_button(
                label="⬇️ Download Markdown",
                data=markdown_content,
                file_name=f"{current_doc.get('title', 'document').lower().replace(' ', '_')}_{st.session_state.current_doc_id}.md",
                mime="text/markdown"
            )
            
            # Copy to clipboard (show formatted text)
            with st.expander("📋 Copy Formatted Text to Clipboard"):
                st.code(markdown_content, language="markdown")
            
            # Document statistics
            st.markdown("---")
            st.subheader("📊 Document Statistics")
            
            word_count = len(markdown_content.split())
            char_count = len(markdown_content)
            
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.metric("Word Count", f"{word_count:,}")
                st.metric("Character Count", f"{char_count:,}")
            
            with col_stats2:
                total_sections = len(current_doc.get('sections', []))
                # Function to count subsections recursively
                def count_subsections_recursive(sections_list):
                    count = 0
                    for s in sections_list:
                        count += len(s.get('subsections', []))
                        count += count_subsections_recursive(s.get('subsections', []))
                    return count
                
                total_subsections = count_subsections_recursive(current_doc.get('sections', []))
                
                # Function to count paragraphs recursively
                def count_paragraphs_recursive(sections_list):
                    count = 0
                    for s in sections_list:
                        count += len(s.get('paragraphs', []))
                        count += count_paragraphs_recursive(s.get('subsections', []))
                    return count
                total_paragraphs = count_paragraphs_recursive(current_doc.get('sections', []))

                st.metric("Top Sections", total_sections)
                st.metric("All Subsections", total_subsections)
                st.metric("All Paragraphs", total_paragraphs) # <--- NEW STATISTIC
                

    # Always show help section at the bottom of the page
    st.markdown("---")
    show_help()

# This is the entry point for the Streamlit page
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Document Editor")
    app_page_1()