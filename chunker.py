# chunker.py
import re
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Chunk:
    id: str
    content: str
    level: str  # 'document', 'section', 'paragraph', 'sentence'
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}

class HierarchicalChunker:
    def __init__(self, doc_id: str, title: str = "", 
                 paragraph_overlap_sentences: int = 2,
                 sentence_overlap_chars: int = 100):
        self.doc_id = doc_id
        self.title = title
        self.chunks = []
        self.chunk_lookup = {}
        self.paragraph_overlap_sentences = paragraph_overlap_sentences
        self.sentence_overlap_chars = sentence_overlap_chars
    
    def chunk_document(self, content: str) -> List[Chunk]:
        """
        Create hierarchical chunks from document content with overlapping
        """
        # Create root document chunk
        doc_chunk = Chunk(
            id=f"{self.doc_id}_doc",
            content=content,
            level="document",
            metadata={
                "title": self.title,
                "word_count": len(content.split()),
                "created_at": datetime.now().isoformat()
            }
        )
        self.chunks.append(doc_chunk)
        self.chunk_lookup[doc_chunk.id] = doc_chunk
        
        # Detect and create section chunks
        sections = self._detect_sections(content)
        
        for section_data in sections:
            section_chunk = self._create_section_chunk(section_data, doc_chunk.id)
            self.chunks.append(section_chunk)
            self.chunk_lookup[section_chunk.id] = section_chunk
            doc_chunk.children_ids.append(section_chunk.id)
            
            # Create overlapping paragraph chunks within each section
            paragraphs = self._detect_paragraphs(section_data['content'])
            overlapping_paras = self._create_overlapping_paragraphs(paragraphs, section_chunk.id)
            
            for para_chunk in overlapping_paras:
                self.chunks.append(para_chunk)
                self.chunk_lookup[para_chunk.id] = para_chunk
                section_chunk.children_ids.append(para_chunk.id)
                
                # Create overlapping sentence chunks within paragraphs
                sentences = self._detect_sentences(para_chunk.metadata['core_content'])
                overlapping_sents = self._create_overlapping_sentences(sentences, para_chunk.id)
                
                for sent_chunk in overlapping_sents:
                    self.chunks.append(sent_chunk)
                    self.chunk_lookup[sent_chunk.id] = sent_chunk
                    para_chunk.children_ids.append(sent_chunk.id)
        
        return self.chunks
    
    def _create_overlapping_paragraphs(self, paragraphs: List[Dict], parent_id: str) -> List[Chunk]:
        """Create paragraph chunks with sentence-level overlapping"""
        overlapping_chunks = []
        
        for i, para_data in enumerate(paragraphs):
            para_id = f"{self.doc_id}_para_{len([c for c in self.chunks if c.level == 'paragraph']) + len(overlapping_chunks)}"
            
            # Get sentences for this paragraph
            para_sentences = self._detect_sentences(para_data['content'])
            
            # Build overlapping content
            overlap_content = para_data['content']
            overlap_info = {"has_overlap": False, "overlap_source": []}
            
            # Add overlap from previous paragraph
            if i > 0 and self.paragraph_overlap_sentences > 0:
                prev_para = paragraphs[i-1]
                prev_sentences = self._detect_sentences(prev_para['content'])
                
                # Take last N sentences from previous paragraph
                if len(prev_sentences) >= self.paragraph_overlap_sentences:
                    overlap_sentences = prev_sentences[-self.paragraph_overlap_sentences:]
                    overlap_text = ' '.join([s['content'] for s in overlap_sentences])
                    overlap_content = f"[Previous context: {overlap_text}] {para_data['content']}"
                    overlap_info["has_overlap"] = True
                    overlap_info["overlap_source"].append(f"prev_para_{self.paragraph_overlap_sentences}_sentences")
            
            # Add overlap from next paragraph  
            if i < len(paragraphs) - 1 and self.paragraph_overlap_sentences > 0:
                next_para = paragraphs[i+1]
                next_sentences = self._detect_sentences(next_para['content'])
                
                # Take first N sentences from next paragraph
                if len(next_sentences) >= self.paragraph_overlap_sentences:
                    overlap_sentences = next_sentences[:self.paragraph_overlap_sentences]
                    overlap_text = ' '.join([s['content'] for s in overlap_sentences])
                    overlap_content = f"{overlap_content} [Following context: {overlap_text}]"
                    overlap_info["has_overlap"] = True
                    overlap_info["overlap_source"].append(f"next_para_{self.paragraph_overlap_sentences}_sentences")
            
            # Get parent section for context
            parent_section = self.chunk_lookup[parent_id]
            section_title = parent_section.metadata.get('title', '')
            
            # Final contextual content
            contextual_content = f"Section: {section_title}\n\n{overlap_content}"
            
            chunk = Chunk(
                id=para_id,
                content=contextual_content,
                level="paragraph",
                parent_id=parent_id,
                metadata={
                    "core_content": para_data['content'],
                    "paragraph_index": para_data['paragraph_index'],
                    "word_count": len(para_data['content'].split()), # Use core_content for word count
                    "has_context": True,
                    "retrievable": True,
                    "overlap_info": overlap_info
                }
            )
            
            overlapping_chunks.append(chunk)
        
        return overlapping_chunks
    
    def _create_overlapping_sentences(self, sentences: List[Dict], parent_id: str) -> List[Chunk]:
        """Create sentence chunks with character-level overlapping"""
        overlapping_chunks = []
        
        for i, sent_data in enumerate(sentences):
            sent_id = f"{self.doc_id}_sent_{len([c for c in self.chunks if c.level == 'sentence']) + len(overlapping_chunks)}"
            
            # Build overlapping content
            overlap_content = sent_data['content']
            overlap_info = {"has_overlap": False, "overlap_source": []}
            
            # Add overlap from previous sentence
            if i > 0 and self.sentence_overlap_chars > 0:
                prev_sent = sentences[i-1]['content']
                # Ensure we don't try to take more chars than available
                overlap_text = prev_sent[-min(self.sentence_overlap_chars, len(prev_sent)):]
                overlap_content = f"...{overlap_text} {sent_data['content']}"
                overlap_info["has_overlap"] = True
                overlap_info["overlap_source"].append(f"prev_sent_{self.sentence_overlap_chars}_chars")
            
            # Add overlap from next sentence
            if i < len(sentences) - 1 and self.sentence_overlap_chars > 0:
                next_sent = sentences[i+1]['content']
                # Ensure we don't try to take more chars than available
                overlap_text = next_sent[:min(self.sentence_overlap_chars, len(next_sent))]
                overlap_content = f"{overlap_content} {overlap_text}..."
                overlap_info["has_overlap"] = True
                overlap_info["overlap_source"].append(f"next_sent_{self.sentence_overlap_chars}_chars")
            
            # Get parent context
            parent_para = self.chunk_lookup[parent_id]
            parent_section = self.chunk_lookup[parent_para.parent_id]
            
            section_title = parent_section.metadata.get('title', '')
            para_content = parent_para.metadata['core_content']
            
            contextual_content = f"Section: {section_title}\n\nParagraph context: {para_content}\n\nSpecific info: {overlap_content}"
            
            chunk = Chunk(
                id=sent_id,
                content=contextual_content,
                level="sentence",
                parent_id=parent_id,
                metadata={
                    "core_content": sent_data['content'],
                    "sentence_index": sent_data['sentence_index'], 
                    "char_count": len(sent_data['content']), # Use core_content for char count
                    "has_context": True,
                    "retrievable": True,
                    "overlap_info": overlap_info
                }
            )
            
            overlapping_chunks.append(chunk)
        
        return overlapping_chunks
    
    def _detect_sections(self, content: str) -> List[Dict]:
        """
        Detect sections based on markdown headers or other patterns
        """
        sections = []
        
        # Split by markdown headers (## or #)
        # We need to handle cases where content starts directly without a header,
        # or where there's content before the first header.
        
        # Regex to find headers and their content
        # Pattern: (## or #) followed by title, then capture everything until the next header or end of string
        section_pattern = r'(?m)^(#{1,3})\s*(.+?)\n(.*?)(?=\n#{1,3}\s*|\Z)'
        
        matches = list(re.finditer(section_pattern, content, re.DOTALL))
        
        # Handle content before the first header
        first_header_start = matches[0].start() if matches else len(content)
        initial_content = content[:first_header_start].strip()
        if initial_content:
            sections.append({
                "title": "Introduction" if "title" not in self.chunk_lookup else f"Introduction_{len(sections)}",
                "content": initial_content,
                "level": 1
            })

        for match in matches:
            header_level_str = match.group(1)
            title = match.group(2).strip()
            section_content = match.group(3).strip()
            
            sections.append({
                "title": title,
                "content": section_content,
                "level": len(header_level_str)
            })
        
        # If no sections found *after* initial content, treat entire content as one section
        if not sections and content.strip():
            sections.append({
                "title": self.title if self.title else "Main Content",
                "content": content,
                "level": 1
            })
            
        return sections
    
    def _detect_paragraphs(self, content: str) -> List[Dict]:
        """
        Split content into paragraphs while preserving structure
        """
        # Split by double newlines (markdown paragraph separator)
        raw_paragraphs = content.split('\n\n')
        
        paragraphs = []
        for i, para in enumerate(raw_paragraphs):
            para = para.strip()
            if para:  # Skip empty paragraphs
                paragraphs.append({
                    "content": para,
                    "paragraph_index": i,
                    "word_count": len(para.split())
                })
        
        return paragraphs
    
    def _detect_sentences(self, content: str) -> List[Dict]:
        """
        Split paragraphs into sentences for fine-grained retrieval
        """
        # Simple sentence splitting (you could use spacy for better results)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        sentence_data = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                sentence_data.append({
                    "content": sentence,
                    "sentence_index": i,
                    "char_count": len(sentence)
                })
        
        return sentence_data
    
    def _create_section_chunk(self, section_data: Dict, parent_id: str) -> Chunk:
        """Create a section-level chunk"""
        # Generate a unique section ID
        section_id = f"{self.doc_id}_section_{len([c for c in self.chunks if c.level == 'section'])}"
        
        return Chunk(
            id=section_id,
            content=f"{'#' * section_data['level']} {section_data['title']}\n\n{section_data['content']}",
            level="section",
            parent_id=parent_id,
            metadata={
                "title": section_data['title'],
                "header_level": section_data['level'],
                "word_count": len(section_data['content'].split()),
                "retrievable": False  # Sections provide context, not direct retrieval
            }
        )
    
    def get_chunk_with_context(self, chunk_id: str, context_level: str = "paragraph") -> str:
        """
        Retrieve a chunk with its hierarchical context
        """
        chunk = self.chunk_lookup.get(chunk_id)
        if not chunk:
            return ""

        # If the requested context level is 'section', traverse up to the section.
        if context_level == "section":
            current = chunk
            while current and current.level != "section":
                current = self.chunk_lookup.get(current.parent_id)
            return current.content if current else chunk.content # Return section content or original if no parent

        # If the requested context level is 'paragraph', get the parent paragraph if the chunk is a sentence.
        # Otherwise, if the chunk itself is a paragraph or higher, just return its content.
        elif context_level == "paragraph":
            if chunk.level == "sentence":
                parent_chunk = self.chunk_lookup.get(chunk.parent_id)
                return parent_chunk.content if parent_chunk else chunk.content
            # If the chunk is already a paragraph or higher, its own content is the paragraph context
            return chunk.content 
        
        # If requested context is 'sentence', or if the chunk is already a sentence
        # (and 'paragraph' or 'section' context was not explicitly requested or found),
        # return the chunk's own content.
        # This implicitly covers `context_level == "sentence"` and the default case.
        return chunk.content
    
    # Removed _create_paragraph_chunk and _create_sentence_chunk as they are
    # now handled by the overlapping specific methods directly in chunk_document or _create_overlapping_paragraphs/sentences

    def get_overlapping_stats(self) -> Dict:
        """Get statistics about overlapping in the chunks"""
        stats = {
            "total_chunks": len(self.chunks),
            "chunks_with_overlap": 0,
            "paragraph_overlaps": 0,
            "sentence_overlaps": 0,
            "overlap_types": {}
        }
        
        for chunk in self.chunks:
            overlap_info = chunk.metadata.get('overlap_info', {})
            if overlap_info.get('has_overlap', False):
                stats["chunks_with_overlap"] += 1
                
                if chunk.level == "paragraph":
                    stats["paragraph_overlaps"] += 1
                elif chunk.level == "sentence":
                    stats["sentence_overlaps"] += 1
                
                for source in overlap_info.get('overlap_source', []):
                    stats["overlap_types"][source] = stats["overlap_types"].get(source, 0) + 1
        
        return stats

def get_chunking_analysis(chunks: List[Chunk]):
    total_chunks = len(chunks)
    
    # Filter for 'retrievable' chunks for analysis that matters for RAG embeddings
    retrievable_chunks = [c for c in chunks if c.metadata.get('retrievable', True)] # Assume retrievable by default if not specified
    
    total_characters = sum(len(c.content) for c in retrievable_chunks)
    avg_chunk_length = total_characters / len(retrievable_chunks) if len(retrievable_chunks) > 0 else 0
    
    # Get a few sample retrievable chunks
    sample_chunks_data = []
    for chunk in retrievable_chunks[:5]: # Take top 5 retrievable chunks
        sample_chunks_data.append({
            "id": chunk.id,
            "level": chunk.level,
            "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "metadata": chunk.metadata
        })

    # Counts by level
    level_counts = {}
    for chunk in chunks:
        level_counts[chunk.level] = level_counts.get(chunk.level, 0) + 1
            
    return {
        "total_chunks": total_chunks,
        "total_retrievable_chunks": len(retrievable_chunks),
        "total_characters_retrievable": total_characters,
        "avg_chunk_length_retrievable": avg_chunk_length,
        "sample_retrievable_chunks": sample_chunks_data,
        "chunk_counts_by_level": level_counts
    }

# The test functions test_overlapping_chunking and test_comprehensive_chunking
# should not be part of the chunker.py if it's meant to be imported as a module
# for a Streamlit app. They are typically for standalone testing.
# For the Streamlit app, we'll only import the class and the get_chunking_analysis function.
# Keep them commented out or in a separate test_chunker.py file.

# if __name__ == "__main__":
#     # This block for local testing of the chunker
#     test_content = """
# # Chapter 1: Introduction to Widgets
# This document outlines the various widgets available in our system. Widgets are essential components for building interactive user interfaces.

# ## Section 1.1: Buttons and Inputs
# Buttons are used to trigger actions. Input fields allow users to enter data. This is a very important part of user interaction.

# A button can be clicked. It performs an action. Users expect immediate feedback.
# Text inputs are for short strings. Text areas are for longer inputs, like comments or descriptions. Numbers are for numerical values.

# ### Sub-section 1.1.1: Button Types
# There are primary buttons and secondary buttons. Primary buttons indicate the most important action. Secondary buttons are for less critical actions.

# ## Section 1.2: Display Widgets
# Display widgets include text, markdown, and images. They are used to present information to the user.

# Displaying data clearly is crucial. Users should easily understand the information presented. Tables and charts can also be considered display widgets.

# # Chapter 2: Advanced Features
# This chapter delves into more complex features of the system.
#     """
#     chunker, chunks = test_overlapping_chunking(test_content)
#     analysis = get_chunking_analysis(chunks)
#     print("\nStreamlit-style analysis output:")
#     print(analysis)