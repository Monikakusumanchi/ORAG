import streamlit as st
import uuid
from datetime import datetime
import json
import re
import os

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

# --- Utility functions ---
def parse_markdown_to_structure(md_content):
    """Parse markdown content into document structure with sections/subsections/paragraphs."""
    lines = md_content.split("\n")
    doc_structure = []
    stack = []  # keep track of section hierarchy

    paragraph_buffer = []

    def flush_paragraphs(current_section):
        nonlocal paragraph_buffer
        if paragraph_buffer:
            for idx, para in enumerate(paragraph_buffer, start=1):
                current_section.setdefault("paragraphs", []).append({
                    "id": generate_unique_id("para"),
                    "order": len(current_section.get("paragraphs", [])) + 1,
                    "content": para.strip()
                })
            paragraph_buffer = []

    for line in lines:
        header_match = re.match(r"^(#+) (.*)", line)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            # Create new section
            new_section = {
                "id": generate_unique_id("section"),
                "title": title,
                "level": level,
                "paragraphs": [],
                "subsections": []
            }

            # Place this section at the right hierarchy level
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            if stack:
                parent = stack[-1]
                flush_paragraphs(parent)
                parent["subsections"].append(new_section)
            else:
                doc_structure.append(new_section)

            stack.append(new_section)
        else:
            if line.strip():
                paragraph_buffer.append(line)
            else:
                if stack:
                    flush_paragraphs(stack[-1])

    # flush leftover paragraphs
    if stack:
        flush_paragraphs(stack[-1])

    return doc_structure

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

# --- Main Streamlit App Page 1 ---
def app_page_1():
    # Initialize session state
    if 'current_doc_id' not in st.session_state:
        st.session_state.current_doc_id = generate_unique_id("doc")
    if 'documents' not in st.session_state:
        st.session_state.documents = {}
    if 'last_uploaded' not in st.session_state:
        st.session_state.last_uploaded = None
    if 'last_saved_path' not in st.session_state:
        st.session_state.last_saved_path = None

    # Ensure current document exists
    if st.session_state.current_doc_id not in st.session_state.documents:
        st.session_state.documents[st.session_state.current_doc_id] = {
            'id': st.session_state.current_doc_id,
            'title': 'New Document',
            'intro': '',
            'sections': []
        }

    current_doc = st.session_state.documents[st.session_state.current_doc_id]

    # Sidebar content
    with st.sidebar:
        st.header("📊 Document Statistics")

        markdown_content_for_stats = generate_markdown_document(current_doc)
        word_count = len(markdown_content_for_stats.split())
        char_count = len(markdown_content_for_stats)

        def count_subsections_recursive(sections_list):
            return sum(len(s.get('subsections', [])) + count_subsections_recursive(s.get('subsections', [])) for s in sections_list)

        def count_paragraphs_recursive(sections_list):
            return sum(len(s.get('paragraphs', [])) + count_paragraphs_recursive(s.get('subsections', [])) for s in sections_list)

        st.metric("Word Count", f"{word_count:,}")
        st.metric("Character Count", f"{char_count:,}")
        st.metric("Top Sections", len(current_doc.get('sections', [])))
        st.metric("All Subsections", count_subsections_recursive(current_doc.get('sections', [])))
        st.metric("All Paragraphs", count_paragraphs_recursive(current_doc.get('sections', [])))

        st.markdown("---")
        if st.button("➕ New Document"):
            new_doc_id = generate_unique_id("doc")
            st.session_state.current_doc_id = new_doc_id
            st.session_state.documents[new_doc_id] = {
                'id': new_doc_id,
                'title': 'New Document',
                'intro': '',
                'sections': []
            }
            st.session_state.last_uploaded = None
            st.session_state.last_saved_path = None
            st.rerun()

        st.markdown("---")
        st.subheader("📂 Available Files (data/)")
        os.makedirs("data", exist_ok=True)
        files = sorted(os.listdir("data"))
        if files:
            for f in files:
                st.text(f)
        else:
            st.info("No files uploaded yet.")

    st.header(f"✏️ Editing: {current_doc.get('title', 'Untitled Document')}")

    # Two column layout for editor and preview
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Document Editor")

        # --- Import Markdown file ---
        st.markdown("### 📂 Import Markdown File")
        uploaded_file = st.file_uploader("Upload a Markdown file", type=["md"])  # implicit upload on selection

        if uploaded_file is not None:
            # Only process/save if this is a new file selection
            if st.session_state.last_uploaded != uploaded_file.name:
                os.makedirs("data", exist_ok=True)
                file_path = os.path.join("data", uploaded_file.name)

                # Save the uploaded file ONCE on new selection
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.last_saved_path = file_path
                st.success(f"✅ File saved to {file_path}")

                # Parse and create a fresh document for this upload
                file_content = uploaded_file.getvalue().decode("utf-8")
                new_doc_id = generate_unique_id("doc")
                st.session_state.current_doc_id = new_doc_id
                st.session_state.documents[new_doc_id] = {
                    'id': new_doc_id,
                    'title': uploaded_file.name.replace(".md", ""),
                    'intro': '',
                    'sections': parse_markdown_to_structure(file_content)
                }
                st.session_state.last_uploaded = uploaded_file.name
                st.rerun()
            else:
                st.info(f"Currently loaded: {st.session_state.last_uploaded}")

        # --- Document Header ---
        st.markdown("### 📄 Document Header")
        title = st.text_input(
            "Document Title",
            value=current_doc.get('title', ''),
            placeholder="Enter document title...",
            key=f"doc_title_{st.session_state.current_doc_id}"
        )
        intro = st.text_area(
            "Introduction",
            value=current_doc.get('intro', ''),
            placeholder="Write an introduction that explains the purpose and scope of this document...",
            height=100,
            key=f"doc_intro_{st.session_state.current_doc_id}"
        )
        current_doc['title'] = title
        current_doc['intro'] = intro

        # --- Sections ---
        st.markdown("### 📚 Sections")
        if st.button("➕ Add New Top-Level Section"):
            add_section()

        def render_section_editor_recursive(sections_list, parent_key_prefix=""):
            for i, section in enumerate(sections_list):
                section_key_prefix = f"{parent_key_prefix}_section_{section['id']}_{i}"
                with st.expander(
                    f"{'📋' if section.get('level', 1) == 1 else '📂'} Section {i+1}: {section.get('title', 'Untitled Section')}",
                    expanded=True
                ):
                    col_title, col_level = st.columns([3, 1])
                    with col_title:
                        section['title'] = st.text_input(
                            "Section Title",
                            value=section.get('title', ''),
                            placeholder="Enter section title...",
                            key=f"title_{section_key_prefix}"
                        )
                    with col_level:
                        section['level'] = st.selectbox(
                            "Heading Level",
                            options=[1, 2, 3, 4],
                            index=min(section.get('level', 1) - 1, 3),
                            key=f"level_{section_key_prefix}"
                        )

                    st.markdown("---")
                    st.markdown(f"**Paragraphs in '{section.get('title', 'Untitled')}'**")
                    if 'paragraphs' not in section:
                        section['paragraphs'] = []

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
                            if st.button("🗑️", key=f"remove_para_{section_key_prefix}_{paragraph['id']}_{p_idx}", help="Remove this paragraph"):
                                remove_paragraph(section['id'], paragraph['id'])

                    if st.button(f"➕ Add Paragraph to '{section.get('title', 'Untitled')}'", key=f"add_para_{section_key_prefix}"):
                        add_paragraph(section['id'])

                    st.markdown("---")
                    st.markdown(f"**Subsections of '{section.get('title', 'Untitled')}'**")
                    if st.button(f"➕ Add Subsection to '{section.get('title', 'Untitled')}'", key=f"add_sub_{section_key_prefix}"):
                        subsection_id = generate_unique_id(f"section_{section['id']}")
                        new_subsection = {
                            'id': subsection_id,
                            'title': f'New Subsection {len(section.get('subsections', [])) + 1}',
                            'level': section.get('level', 1) + 1,
                            'paragraphs': [],
                            'subsections': []
                        }
                        section.setdefault('subsections', []).append(new_subsection)
                        st.rerun()

                    if section.get('subsections'):
                        render_section_editor_recursive(section['subsections'], parent_key_prefix=section_key_prefix)

                    st.markdown("---")
                    if st.button(f"🗑️ Remove Section '{section.get('title', 'Untitled')}'", key=f"remove_section_{section_key_prefix}"):
                        if parent_key_prefix == "":
                            st.session_state.documents[st.session_state.current_doc_id]['sections'].pop(i)
                        else:
                            st.warning("Nested section removal not fully implemented.")
                        st.rerun()

        if current_doc.get('sections'):
            render_section_editor_recursive(current_doc['sections'])
        else:
            st.info("👆 Add a new top-level section to start building your document structure.")

    with col2:
        st.subheader("👁️ Live Preview")
        markdown_content = generate_markdown_document(current_doc)

        if markdown_content.strip():
            st.markdown("#### 📖 Document Preview:")
            st.markdown(markdown_content)
        else:
            st.info("👆 Start adding content on the left to see your document preview here!")

        st.markdown("---")
        st.subheader("💾 Export Options")
        if markdown_content.strip():
            if st.button("💾 Explicitly Save Document"):
                save_document()
                st.success(f"✅ Document '{current_doc.get('title', 'Untitled')}' saved!")

            st.download_button(
                label="⬇️ Download Markdown",
                data=markdown_content,
                file_name=f"{current_doc.get('title', 'document').lower().replace(' ', '_')}_{st.session_state.current_doc_id}.md",
                mime="text/markdown"
            )

            # Save an extra copy ONLY when the user asks for it
            if st.button("📂 Save a copy to data/ for chunking"):
                os.makedirs("data", exist_ok=True)
                save_path = os.path.join(
                    "data",
                    f"{current_doc.get('title', 'document').lower().replace(' ', '_')}_{st.session_state.current_doc_id}.md"
                )
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                st.session_state.last_saved_path = save_path
                st.success(f"📁 Saved to: {save_path}")

            with st.expander("📋 Copy Formatted Text to Clipboard"):
                st.code(markdown_content, language="markdown")

    st.markdown("---")
    show_help()

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Document Editor")
    app_page_1()
