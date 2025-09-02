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
                    "word_count": para_data['word_count'],
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
                if len(prev_sent) >= self.sentence_overlap_chars:
                    overlap_text = prev_sent[-self.sentence_overlap_chars:]
                    overlap_content = f"...{overlap_text} {sent_data['content']}"
                    overlap_info["has_overlap"] = True
                    overlap_info["overlap_source"].append(f"prev_sent_{self.sentence_overlap_chars}_chars")
            
            # Add overlap from next sentence
            if i < len(sentences) - 1 and self.sentence_overlap_chars > 0:
                next_sent = sentences[i+1]['content']
                if len(next_sent) >= self.sentence_overlap_chars:
                    overlap_text = next_sent[:self.sentence_overlap_chars]
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
                    "char_count": sent_data['char_count'],
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

def test_overlapping_chunking(test_content):
    """
    Test the enhanced chunker with overlapping capabilities
    """
    print("=" * 60)
    print("TESTING ENHANCED CHUNKER WITH OVERLAPPING")
    print("=" * 60)
    
    # Test with different overlap settings
    chunker = HierarchicalChunker(
        "test_doc", 
        "Test Employee Handbook",
        paragraph_overlap_sentences=2,  # 2 sentences overlap between paragraphs
        sentence_overlap_chars=80       # 80 characters overlap between sentences
    )
    
    chunks = chunker.chunk_document(test_content)
    
    # Show results
    print(f"Total chunks created: {len(chunks)}")
    
    # Show overlap statistics
    overlap_stats = chunker.get_overlapping_stats()
    print(f"\n{'='*40}")
    print("OVERLAPPING STATISTICS")
    print(f"{'='*40}")
    print(f"Total chunks: {overlap_stats['total_chunks']}")
    print(f"Chunks with overlap: {overlap_stats['chunks_with_overlap']}")
    print(f"Paragraph overlaps: {overlap_stats['paragraph_overlaps']}")
    print(f"Sentence overlaps: {overlap_stats['sentence_overlaps']}")
    
    print(f"\nOverlap types:")
    for overlap_type, count in overlap_stats['overlap_types'].items():
        print(f"  {overlap_type}: {count}")
    
    # Show examples of overlapping chunks
    print(f"\n{'='*40}")
    print("OVERLAP EXAMPLES")
    print(f"{'='*40}")
    
    # Find paragraph chunks with overlap
    para_chunks = [c for c in chunks if c.level == "paragraph" and c.metadata.get('overlap_info', {}).get('has_overlap')]
    
    if para_chunks:
        print(f"\n🔄 PARAGRAPH WITH OVERLAP EXAMPLE:")
        sample_para = para_chunks[0]
        print(f"ID: {sample_para.id}")
        print(f"Overlap sources: {sample_para.metadata['overlap_info']['overlap_source']}")
        print(f"Content (first 400 chars):\n{sample_para.content[:400]}...")
        
        print(f"\nCore content only:\n{sample_para.metadata['core_content'][:200]}...")
    
    # Find sentence chunks with overlap
    sent_chunks = [c for c in chunks if c.level == "sentence" and c.metadata.get('overlap_info', {}).get('has_overlap')]
    
    if sent_chunks:
        print(f"\n🎯 SENTENCE WITH OVERLAP EXAMPLE:")
        sample_sent = sent_chunks[0]
        print(f"ID: {sample_sent.id}")
        print(f"Overlap sources: {sample_sent.metadata['overlap_info']['overlap_source']}")
        print(f"Core sentence: {sample_sent.metadata['core_content']}")
        print(f"Full contextual content:\n{sample_sent.content}")
    
    print(f"\n{'='*60}")
    print("BENEFITS OF THIS OVERLAPPING APPROACH")
    print(f"{'='*60}")
    print("✅ Context preservation across chunk boundaries")
    print("✅ Better semantic continuity for embeddings")
    print("✅ Improved retrieval accuracy")
    print("✅ Redundancy for robustness")
    print("✅ Configurable overlap levels")
    print("✅ Metadata tracking of overlap sources")
    
    return chunker, chunks


# if __name__ == "__main__":
#     chunker, chunks = test_overlapping_chunking()
    
#     print(f"\n{'='*60}")
#     print("CONFIGURATION RECOMMENDATIONS")
#     print(f"{'='*60}")
    
#     recommendations = get_overlap_recommendations()
#     for doc_type, config in recommendations.items():
#         print(f"\n📋 {doc_type.replace('_', ' ').title()}:")
#         print(f"   Paragraph overlap: {config['paragraph_overlap_sentences']} sentences")
#         print(f"   Sentence overlap: {config['sentence_overlap_chars']} characters")
#         print(f"   Reasoning: {config['reasoning']}")

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
    chunker, chunks = test_overlapping_chunking(test_content)