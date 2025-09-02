import streamlit as st
import uuid
from datetime import datetime
import json
import re

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'current_doc_id' not in st.session_state:
    st.session_state.current_doc_id = None
if 'sections' not in st.session_state:
    st.session_state.sections = []

def generate_doc_id():
    """Generate a unique document ID"""
    return str(uuid.uuid4())[:8]

def create_new_document():
    """Initialize a new document structure"""
    doc_id = generate_doc_id()
    st.session_state.current_doc_id = doc_id
    st.session_state.sections = []
    
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
    """Add a new section to current document"""
    section_id = f"section_{len(st.session_state.sections) + 1}"
    new_section = {
        'id': section_id,
        'title': '',
        'level': 1,  # Default to h1
        'subsections': []
    }
    st.session_state.sections.append(new_section)

def add_subsection(parent_section_idx):
    """Add a subsection to a parent section"""
    subsection_id = f"subsection_{len(st.session_state.sections[parent_section_idx]['subsections']) + 1}"
    new_subsection = {
        'id': subsection_id,
        'title': '',
        'content': '',
        'level': 2  # Default to h2
    }
    st.session_state.sections[parent_section_idx]['subsections'].append(new_subsection)

def generate_markdown_document(doc_data):
    """Generate the final markdown document"""
    markdown_content = f"# {doc_data['title']}\n\n"
    
    if doc_data['intro']:
        markdown_content += f"{doc_data['intro']}\n\n"
    
    for section in doc_data['sections']:
        # Add main section
        section_header = "#" * section['level']
        markdown_content += f"{section_header} {section['title']}\n\n"
        
        # Add subsections
        for subsection in section['subsections']:
            subsection_header = "#" * subsection['level']
            markdown_content += f"{subsection_header} {subsection['title']}\n\n"
            if subsection['content']:
                markdown_content += f"{subsection['content']}\n\n"
    
    return markdown_content

def save_document():
    """Save current document to session state"""
    if st.session_state.current_doc_id:
        st.session_state.documents[st.session_state.current_doc_id]['sections'] = st.session_state.sections
        st.session_state.documents[st.session_state.current_doc_id]['last_modified'] = datetime.now().isoformat()

# Streamlit App
def main():
    st.set_page_config(
        page_title="Document Creator for Hierarchical Chunking",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 Document Creator")
    st.markdown("Create well-structured documents optimized for hierarchical chunking and RAG systems")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("📋 Document Management")
        
        # Create new document button
        if st.button("🆕 Create New Document", type="primary"):
            create_new_document()
            st.rerun()
        
        # Show existing documents
        if st.session_state.documents:
            st.subheader("📚 Your Documents")
            for doc_id, doc in st.session_state.documents.items():
                if st.button(f"📄 {doc.get('title', 'Untitled')} ({doc_id})"):
                    st.session_state.current_doc_id = doc_id
                    st.session_state.sections = doc.get('sections', [])
                    st.rerun()
    
    # Main content area
    if not st.session_state.current_doc_id:
        # Welcome screen
        st.markdown("""
        ## Welcome to Document Creator! 👋
        
        This tool helps you create well-structured documents that work perfectly with hierarchical chunking systems.
        
        ### 🎯 Features:
        - **Structured Format**: Consistent heading hierarchy for optimal chunking
        - **Real-time Preview**: See your document as you build it
        - **Export Options**: Download as Markdown or copy formatted text
        - **Template Library**: Pre-built templates for common document types
        
        ### 📋 Document Types Supported:
        - Employee Handbooks
        - Policy Documents  
        - Technical Documentation
        - Training Manuals
        - Standard Operating Procedures
        
        **Click "Create New Document" in the sidebar to get started!**
        """)
        
        # Template selection
        st.subheader("🚀 Quick Start Templates")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Employee Handbook"):
                doc_id = create_new_document()
                st.session_state.documents[doc_id].update({
                    'title': 'Employee Handbook',
                    'intro': 'Welcome to our company! This handbook contains important policies and procedures.',
                    'sections': [
                        {'id': 'section_1', 'title': 'Company Overview', 'level': 1, 'subsections': []},
                        {'id': 'section_2', 'title': 'Employment Policies', 'level': 1, 'subsections': []},
                        {'id': 'section_3', 'title': 'Benefits and Compensation', 'level': 1, 'subsections': []}
                    ]
                })
                st.session_state.sections = st.session_state.documents[doc_id]['sections']
                st.rerun()
        
        with col2:
            if st.button("🔧 Technical Manual"):
                doc_id = create_new_document()
                st.session_state.documents[doc_id].update({
                    'title': 'Technical Documentation',
                    'intro': 'This technical manual provides comprehensive guidance for system implementation and maintenance.',
                    'sections': [
                        {'id': 'section_1', 'title': 'Getting Started', 'level': 1, 'subsections': []},
                        {'id': 'section_2', 'title': 'Installation Guide', 'level': 1, 'subsections': []},
                        {'id': 'section_3', 'title': 'Configuration', 'level': 1, 'subsections': []}
                    ]
                })
                st.session_state.sections = st.session_state.documents[doc_id]['sections']
                st.rerun()
        
        with col3:
            if st.button("📊 Policy Document"):
                doc_id = create_new_document()
                st.session_state.documents[doc_id].update({
                    'title': 'Company Policies',
                    'intro': 'This document outlines important company policies and procedures that all employees must follow.',
                    'sections': [
                        {'id': 'section_1', 'title': 'Code of Conduct', 'level': 1, 'subsections': []},
                        {'id': 'section_2', 'title': 'Safety Policies', 'level': 1, 'subsections': []},
                        {'id': 'section_3', 'title': 'IT Security', 'level': 1, 'subsections': []}
                    ]
                })
                st.session_state.sections = st.session_state.documents[doc_id]['sections']
                st.rerun()
        
    else:
        # Document editing interface
        current_doc = st.session_state.documents[st.session_state.current_doc_id]
        
        st.header(f"✏️ Editing: {current_doc.get('title', 'Untitled Document')}")
        
        # Two column layout
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
                    key="doc_title"
                )
                
                intro = st.text_area(
                    "Introduction",
                    value=current_doc.get('intro', ''),
                    placeholder="Write an introduction that explains the purpose and scope of this document...",
                    height=100,
                    key="doc_intro"
                )
                
                # Update document
                current_doc['title'] = title
                current_doc['intro'] = intro
            
            # Sections management
            st.markdown("### 📚 Sections")
            
            # Add section button
            if st.button("➕ Add New Section"):
                add_section()
                st.rerun()
            
            # Edit existing sections
            for i, section in enumerate(st.session_state.sections):
                with st.expander(f"📋 Section {i+1}: {section.get('title', 'Untitled')}", expanded=True):
                    
                    # Section title and level
                    col_title, col_level = st.columns([3, 1])
                    
                    with col_title:
                        section_title = st.text_input(
                            "Section Title",
                            value=section.get('title', ''),
                            placeholder="Enter section title...",
                            key=f"section_title_{i}"
                        )
                        section['title'] = section_title
                    
                    with col_level:
                        section_level = st.selectbox(
                            "Heading Level",
                            options=[1, 2, 3],
                            index=section.get('level', 1) - 1,
                            key=f"section_level_{i}"
                        )
                        section['level'] = section_level
                    
                    # Subsections
                    st.markdown("**Subsections:**")
                    
                    if st.button(f"➕ Add Subsection", key=f"add_subsection_{i}"):
                        add_subsection(i)
                        st.rerun()
                    
                    # Edit subsections
                    for j, subsection in enumerate(section['subsections']):
                        with st.container():
                            st.markdown(f"*Subsection {j+1}:*")
                            
                            subsection_title = st.text_input(
                                "Subsection Title",
                                value=subsection.get('title', ''),
                                placeholder="Enter subsection title...",
                                key=f"subsection_title_{i}_{j}"
                            )
                            subsection['title'] = subsection_title
                            
                            subsection_content = st.text_area(
                                "Content",
                                value=subsection.get('content', ''),
                                placeholder="Write the content for this subsection. Use multiple paragraphs for better chunking...",
                                height=150,
                                key=f"subsection_content_{i}_{j}"
                            )
                            subsection['content'] = subsection_content
                            
                            if st.button(f"🗑️ Remove Subsection", key=f"remove_subsection_{i}_{j}"):
                                section['subsections'].pop(j)
                                st.rerun()
                            
                            st.markdown("---")
                    
                    if st.button(f"🗑️ Remove Section {i+1}", key=f"remove_section_{i}"):
                        st.session_state.sections.pop(i)
                        st.rerun()
        
        with col2:
            st.subheader("👁️ Live Preview")
            
            # Generate and show preview
            current_doc['sections'] = st.session_state.sections
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
                # Save document
                if st.button("💾 Save Document"):
                    save_document()
                    st.success(f"✅ Document saved! ID: {st.session_state.current_doc_id}")
                
                # Download as markdown
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=markdown_content,
                    file_name=f"{current_doc.get('title', 'document').lower().replace(' ', '_')}.md",
                    mime="text/markdown"
                )
                
                # Copy to clipboard (show formatted text)
                with st.expander("📋 Copy Formatted Text"):
                    st.code(markdown_content, language="markdown")
                
                # Show chunking preview
                with st.expander("🔍 Chunking Preview"):
                    st.markdown("**How this document will be chunked:**")
                    
                    # Simulate chunking analysis
                    sections_count = len([line for line in markdown_content.split('\n') if line.startswith('#')])
                    paragraphs_count = len([p for p in markdown_content.split('\n\n') if p.strip()])
                    sentences_count = len(re.findall(r'[.!?]+', markdown_content))
                    
                    st.markdown(f"""
                    - **Document Level**: 1 chunk (entire document)
                    - **Section Level**: ~{sections_count} chunks (main sections)
                    - **Paragraph Level**: ~{paragraphs_count} chunks (retrievable)
                    - **Sentence Level**: ~{sentences_count} chunks (retrievable)
                    
                    **Total Retrievable Chunks**: ~{paragraphs_count + sentences_count}
                    """)
            
            # Document statistics
            if markdown_content.strip():
                st.markdown("---")
                st.subheader("📊 Document Statistics")
                
                word_count = len(markdown_content.split())
                char_count = len(markdown_content)
                
                col_stats1, col_stats2 = st.columns(2)
                with col_stats1:
                    st.metric("Word Count", f"{word_count:,}")
                    st.metric("Character Count", f"{char_count:,}")
                
                with col_stats2:
                    st.metric("Sections", len(st.session_state.sections))
                    total_subsections = sum(len(s['subsections']) for s in st.session_state.sections)
                    st.metric("Subsections", total_subsections)

# Document templates
def load_template(template_type):
    """Load predefined templates"""
    templates = {
        "employee_handbook": {
            "title": "Employee Handbook",
            "intro": "Welcome to our organization! This handbook serves as your comprehensive guide to company policies, procedures, benefits, and workplace expectations. Please read through this document carefully and refer to it whenever you have questions about your employment.",
            "sections": [
                {
                    "id": "company_overview",
                    "title": "Company Overview",
                    "level": 1,
                    "subsections": [
                        {"id": "mission", "title": "Mission and Values", "level": 2, "content": "Our mission is to [insert mission statement]. We are guided by core values of integrity, innovation, collaboration, and customer focus."},
                        {"id": "history", "title": "Company History", "level": 2, "content": "Founded in [year], our company has grown from [origin story] to become [current status]."}
                    ]
                },
                {
                    "id": "employment_policies",
                    "title": "Employment Policies", 
                    "level": 1,
                    "subsections": [
                        {"id": "equal_opportunity", "title": "Equal Opportunity Employment", "level": 2, "content": "We are an equal opportunity employer committed to creating an inclusive workplace for all employees."},
                        {"id": "at_will", "title": "At-Will Employment", "level": 2, "content": "Employment is at-will, meaning either party may terminate the relationship at any time."}
                    ]
                },
                {
                    "id": "work_schedule",
                    "title": "Work Hours and Attendance",
                    "level": 1,
                    "subsections": [
                        {"id": "standard_hours", "title": "Standard Work Schedule", "level": 2, "content": "Standard business hours are 9:00 AM to 5:00 PM, Monday through Friday."},
                        {"id": "remote_work", "title": "Remote Work Policy", "level": 2, "content": "Remote work is available [specify conditions and requirements]."}
                    ]
                }
            ]
        },
        "technical_manual": {
            "title": "Technical Documentation",
            "intro": "This technical manual provides comprehensive guidance for system implementation, configuration, and maintenance. It is designed for technical professionals and system administrators.",
            "sections": [
                {
                    "id": "getting_started",
                    "title": "Getting Started",
                    "level": 1,
                    "subsections": [
                        {"id": "prerequisites", "title": "Prerequisites", "level": 2, "content": "Before beginning installation, ensure your system meets the following requirements: [list requirements]."},
                        {"id": "overview", "title": "System Overview", "level": 2, "content": "This system provides [describe functionality and purpose]."}
                    ]
                },
                {
                    "id": "installation",
                    "title": "Installation Guide",
                    "level": 1,
                    "subsections": [
                        {"id": "download", "title": "Download and Setup", "level": 2, "content": "Download the installation package from [source] and follow these steps: [detailed steps]."},
                        {"id": "configuration", "title": "Initial Configuration", "level": 2, "content": "Configure the system using the following parameters: [configuration details]."}
                    ]
                }
            ]
        },
        "policy_document": {
            "title": "Company Policies and Procedures",
            "intro": "This document outlines important company policies and procedures that all employees must understand and follow. These policies ensure a safe, productive, and compliant work environment.",
            "sections": [
                {
                    "id": "conduct_policies",
                    "title": "Code of Conduct",
                    "level": 1,
                    "subsections": [
                        {"id": "professional_behavior", "title": "Professional Behavior", "level": 2, "content": "All employees are expected to maintain professional conduct in all business interactions."},
                        {"id": "harassment_policy", "title": "Anti-Harassment Policy", "level": 2, "content": "We maintain a zero-tolerance policy for harassment of any kind."}
                    ]
                },
                {
                    "id": "safety_policies",
                    "title": "Workplace Safety",
                    "level": 1,
                    "subsections": [
                        {"id": "general_safety", "title": "General Safety Guidelines", "level": 2, "content": "All employees must follow established safety procedures to maintain a safe work environment."},
                        {"id": "emergency_procedures", "title": "Emergency Procedures", "level": 2, "content": "In case of emergency, follow these established procedures: [emergency steps]."}
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
        - Use logical heading levels (H1 for main sections, H2 for subsections)
        - Keep section titles concise and descriptive
        - Maintain consistent formatting throughout
        
        **2. Content Guidelines**
        - Write clear, complete paragraphs (50-200 words ideal)
        - Use specific, factual language
        - Include relevant details and context
        - Break up long content into subsections
        
        **3. Chunking Optimization**
        - Each subsection should cover one complete topic
        - Avoid splitting related information across sections
        - Include enough context for standalone understanding
        - Use descriptive headings that indicate content
        
        **4. Examples of Good Section Content**:
        ```
        ## Vacation Policy
        
        Full-time employees accrue vacation time based on their length of service. 
        New employees (0-2 years) earn 2.5 days per month, totaling 20 days annually.
        
        Vacation requests must be submitted at least two weeks in advance through 
        the HR portal. Manager approval is required, and requests are subject to 
        business needs and adequate coverage requirements.
        ```
        
        **5. Content That Works Well for RAG**:
        - Policy explanations with specific details
        - Step-by-step procedures
        - Requirements and specifications
        - Examples and use cases
        """)

def main_app():
    """Main application logic"""
    main()
    
    # Show help section
    show_help()
    
    # Document management
    if st.session_state.current_doc_id:
        current_doc = st.session_state.documents[st.session_state.current_doc_id]
        
        # Auto-save on changes
        save_document()
        
        # Show document metadata
        with st.sidebar:
            st.markdown("---")
            st.subheader("📋 Document Info")
            st.text(f"ID: {current_doc['id']}")
            st.text(f"Created: {current_doc['created_at'][:19]}")
            st.text(f"Modified: {current_doc['last_modified'][:19]}")
            
            # Export all documents
            if st.button("📦 Export All Documents"):
                all_docs_json = json.dumps(st.session_state.documents, indent=2)
                st.download_button(
                    "⬇️ Download All as JSON",
                    data=all_docs_json,
                    file_name="all_documents.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main_app()