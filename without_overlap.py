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
    def __init__(self, doc_id: str, title: str = ""):
        self.doc_id = doc_id
        self.title = title
        self.chunks = []
        self.chunk_lookup = {}
    
    def chunk_document(self, content: str) -> List[Chunk]:
        """
        Create hierarchical chunks from document content
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
            
            # Create paragraph chunks within each section
            paragraphs = self._detect_paragraphs(section_data['content'])
            
            for para_data in paragraphs:
                para_chunk = self._create_paragraph_chunk(para_data, section_chunk.id)
                self.chunks.append(para_chunk)
                self.chunk_lookup[para_chunk.id] = para_chunk
                section_chunk.children_ids.append(para_chunk.id)
                
                # Create sentence chunks within paragraphs (for precise retrieval)
                sentences = self._detect_sentences(para_data['content'])
                
                for sent_data in sentences:
                    sent_chunk = self._create_sentence_chunk(sent_data, para_chunk.id)
                    self.chunks.append(sent_chunk)
                    self.chunk_lookup[sent_chunk.id] = sent_chunk
                    para_chunk.children_ids.append(sent_chunk.id)
        
        return self.chunks
    
    def _detect_sections(self, content: str) -> List[Dict]:
        """
        Detect sections based on markdown headers or other patterns
        """
        sections = []
        
        # Split by markdown headers (## or #)
        parts = re.split(r'\n(#{1,3})\s+(.+)\n', content)
        
        current_section = {"title": "", "content": "", "level": 1}
        
        for i in range(len(parts)):
            if i % 3 == 0:  # Content part
                if parts[i].strip():
                    current_section["content"] += parts[i].strip() + "\n"
            elif i % 3 == 1:  # Header level (# ## ###)
                if current_section["content"]:
                    sections.append(current_section.copy())
                
                header_level = len(parts[i])
                current_section = {
                    "title": parts[i+1] if i+1 < len(parts) else "",
                    "content": "",
                    "level": header_level
                }
        
        # Add final section
        if current_section["content"]:
            sections.append(current_section)
        
        # If no sections found, treat entire content as one section
        if not sections:
            sections = [{
                "title": "Main Content",
                "content": content,
                "level": 1
            }]
        
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
        section_id = f"{self.doc_id}_section_{len([c for c in self.chunks if c.level == 'section'])}"
        
        return Chunk(
            id=section_id,
            content=f"# {section_data['title']}\n\n{section_data['content']}",
            level="section",
            parent_id=parent_id,
            metadata={
                "title": section_data['title'],
                "header_level": section_data['level'],
                "word_count": len(section_data['content'].split()),
                "retrievable": False  # Sections provide context, not direct retrieval
            }
        )
    
    def _create_paragraph_chunk(self, para_data: Dict, parent_id: str) -> Chunk:
        """Create a paragraph-level chunk with contextual overlap"""
        para_id = f"{self.doc_id}_para_{len([c for c in self.chunks if c.level == 'paragraph'])}"
        
        # Get parent section for context
        parent_section = self.chunk_lookup[parent_id]
        section_title = parent_section.metadata.get('title', '')
        
        # Add section context to paragraph for better embeddings
        contextual_content = f"Section: {section_title}\n\n{para_data['content']}"
        
        return Chunk(
            id=para_id,
            content=contextual_content,
            level="paragraph", 
            parent_id=parent_id,
            metadata={
                "core_content": para_data['content'],  # Original paragraph without context
                "paragraph_index": para_data['paragraph_index'],
                "word_count": para_data['word_count'],
                "has_context": True,
                "retrievable": True  # Paragraphs are good for general retrieval
            }
        )
    
    def _create_sentence_chunk(self, sent_data: Dict, parent_id: str) -> Chunk:
        """Create sentence-level chunk with paragraph context"""
        sent_id = f"{self.doc_id}_sent_{len([c for c in self.chunks if c.level == 'sentence'])}"
        
        # Get parent paragraph and section for context
        parent_para = self.chunk_lookup[parent_id]
        parent_section = self.chunk_lookup[parent_para.parent_id]
        
        # Build contextual sentence (sentence + surrounding context)
        section_title = parent_section.metadata.get('title', '')
        para_content = parent_para.metadata['core_content']
        
        contextual_content = f"Section: {section_title}\n\nContext: {para_content}\n\nSpecific info: {sent_data['content']}"
        
        return Chunk(
            id=sent_id,
            content=contextual_content,
            level="sentence",
            parent_id=parent_id,
            metadata={
                "core_content": sent_data['content'],
                "sentence_index": sent_data['sentence_index'], 
                "char_count": sent_data['char_count'],
                "has_context": True,
                "retrievable": True  # Sentences for precise retrieval
            }
        )
    
    def get_chunk_with_context(self, chunk_id: str, context_level: str = "paragraph") -> str:
        """
        Retrieve a chunk with its hierarchical context
        """
        chunk = self.chunk_lookup.get(chunk_id)
        if not chunk:
            return ""
        
        if context_level == "sentence" or chunk.level == "sentence":
            return chunk.content
        elif context_level == "paragraph":
            # If it's a sentence, get parent paragraph
            if chunk.level == "sentence":
                parent_chunk = self.chunk_lookup.get(chunk.parent_id)
                return parent_chunk.content if parent_chunk else chunk.content
            return chunk.content
        elif context_level == "section":
            # Traverse up to section level
            current = chunk
            while current and current.level != "section":
                current = self.chunk_lookup.get(current.parent_id)
            return current.content if current else chunk.content
        
        return chunk.content

def test_comprehensive_chunking(comprehensive_employee_handbook):
    """
    Test hierarchical chunking with a substantial document
    """
    from datetime import datetime
    
    # Initialize chunker
    chunker = HierarchicalChunker("employee_handbook", "TechCorp Solutions Employee Handbook")
    
    # Process the document
    chunks = chunker.chunk_document(comprehensive_employee_handbook)
    
    # Analyze results
    print("=" * 60)
    print("COMPREHENSIVE EMPLOYEE HANDBOOK CHUNKING ANALYSIS")
    print("=" * 60)
    
    # Count chunks by level
    level_counts = {}
    for chunk in chunks:
        level_counts[chunk.level] = level_counts.get(chunk.level, 0) + 1
    
    print(f"\nTotal chunks created: {len(chunks)}")
    for level, count in level_counts.items():
        print(f"  {level.title()} level: {count} chunks")
    
    # Show document structure
    print(f"\n{'='*40}")
    print("DOCUMENT HIERARCHY")
    print(f"{'='*40}")
    
    doc_chunk = next(c for c in chunks if c.level == "document")
    print(f"📄 Document: {doc_chunk.metadata['title']}")
    print(f"   Word count: {doc_chunk.metadata['word_count']:,}")
    
    # Show sections
    section_chunks = [c for c in chunks if c.level == "section"]
    for section in section_chunks:
        print(f"\n📚 Section: {section.metadata['title']}")
        
        # Count paragraphs in this section
        para_children = [chunker.chunk_lookup[child_id] for child_id in section.children_ids]
        print(f"   └── {len(para_children)} paragraphs")
        
        # Count sentences in this section
        sentence_count = 0
        for para in para_children:
            sentence_count += len(para.children_ids)
        print(f"   └── {sentence_count} sentences")
    
    # Show retrievable chunks statistics
    retrievable_chunks = [c for c in chunks if c.metadata.get('retrievable', False)]
    print(f"\n{'='*40}")
    print("RETRIEVABLE CHUNKS FOR EMBEDDING")
    print(f"{'='*40}")
    print(f"Total retrievable chunks: {len(retrievable_chunks)}")
    
    para_chunks = [c for c in retrievable_chunks if c.level == "paragraph"]
    sent_chunks = [c for c in retrievable_chunks if c.level == "sentence"]
    
    print(f"  Paragraph chunks: {len(para_chunks)}")
    print(f"  Sentence chunks: {len(sent_chunks)}")
    
    # Show example chunks with context
    print(f"\n{'='*40}")
    print("SAMPLE RETRIEVABLE CHUNKS")
    print(f"{'='*40}")
    
    # Show a paragraph chunk example
    if para_chunks:
        sample_para = para_chunks[5] if len(para_chunks) > 5 else para_chunks[0]
        print(f"\n🔍 PARAGRAPH CHUNK EXAMPLE:")
        print(f"ID: {sample_para.id}")
        print(f"Level: {sample_para.level}")
        print(f"Word count: {sample_para.metadata['word_count']}")
        print(f"Content preview:\n{sample_para.content[:300]}...")
    
    # Show a sentence chunk example
    if sent_chunks:
        sample_sent = sent_chunks[10] if len(sent_chunks) > 10 else sent_chunks[0]
        print(f"\n🎯 SENTENCE CHUNK EXAMPLE:")
        print(f"ID: {sample_sent.id}")
        print(f"Level: {sample_sent.level}")
        print(f"Core content: {sample_sent.metadata['core_content']}")
        print(f"Full contextual content:\n{sample_sent.content[:400]}...")
    
    # Test context retrieval
    print(f"\n{'='*40}")
    print("CONTEXT RETRIEVAL TEST")
    print(f"{'='*40}")
    
    if sent_chunks:
        test_sentence = sent_chunks[5] if len(sent_chunks) > 5 else sent_chunks[0]
        
        print(f"Testing context retrieval for: {test_sentence.id}")
        print(f"Original sentence: {test_sentence.metadata['core_content']}")
        
        # Get different context levels
        sentence_context = chunker.get_chunk_with_context(test_sentence.id, "sentence")
        paragraph_context = chunker.get_chunk_with_context(test_sentence.id, "paragraph")
        section_context = chunker.get_chunk_with_context(test_sentence.id, "section")
        
        print(f"\nSentence level context length: {len(sentence_context)} chars")
        print(f"Paragraph level context length: {len(paragraph_context)} chars")
        print(f"Section level context length: {len(section_context)} chars")
    
    return chunker, chunks

if __name__ == "__main__":
    with open('sample.txt', 'r', encoding='utf-8') as file:
        test_content = file.read()
    print("✅ Successfully loaded content from sample.txt")
    print(f"Content length: {len(test_content)} characters")
    chunker, chunks = test_comprehensive_chunking(test_content)
    
    print(f"\n{'='*60}")
    print("CHUNKING COMPLETE - READY FOR EMBEDDING PIPELINE")
    print(f"{'='*60}")
    
    retrievable_chunks = [c for c in chunks if c.metadata.get('retrievable', False)]
    print(f"Ready to embed {len(retrievable_chunks)} chunks into vector database")
    print(f"Document processed: {chunker.title}")
    print(f"Total processing time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")