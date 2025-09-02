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
    level: str  # 'document', 'section', 'paragraph', 'sentence', 'fixed'
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
                 sentence_overlap_chars: int = 100,
                 strategy: str = "hierarchical_overlap",  # default
                 fixed_chunk_size: int = 200):
        """
        strategy: 'hierarchical', 'hierarchical_overlap', 'fixed_size'
        """
        self.doc_id = doc_id
        self.title = title
        self.chunks = []
        self.chunk_lookup = {}
        self.paragraph_overlap_sentences = paragraph_overlap_sentences
        self.sentence_overlap_chars = sentence_overlap_chars
        self.strategy = strategy
        self.fixed_chunk_size = fixed_chunk_size

    def chunk_document(self, content: str) -> List[Chunk]:
        """Create chunks depending on strategy"""
        if self.strategy == "fixed_size":
            return self._fixed_size_chunking(content)

        return self._hierarchical_chunking(content, overlap=(self.strategy == "hierarchical_overlap"))

    # ------------------ Hierarchical Chunking -------------------
    def _hierarchical_chunking(self, content: str, overlap: bool = True) -> List[Chunk]:
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

        # Detect sections
        sections = self._detect_sections(content)

        for section_data in sections:
            section_chunk = self._create_section_chunk(section_data, doc_chunk.id)
            self.chunks.append(section_chunk)
            self.chunk_lookup[section_chunk.id] = section_chunk
            doc_chunk.children_ids.append(section_chunk.id)

            # Paragraphs
            paragraphs = self._detect_paragraphs(section_data['content'])

            if overlap:
                para_chunks = self._create_overlapping_paragraphs(paragraphs, section_chunk.id)
            else:
                para_chunks = self._create_plain_paragraphs(paragraphs, section_chunk.id)

            for para_chunk in para_chunks:
                self.chunks.append(para_chunk)
                self.chunk_lookup[para_chunk.id] = para_chunk
                section_chunk.children_ids.append(para_chunk.id)

                # Sentences
                sentences = self._detect_sentences(para_chunk.metadata['core_content'])

                if overlap:
                    sent_chunks = self._create_overlapping_sentences(sentences, para_chunk.id)
                else:
                    sent_chunks = self._create_plain_sentences(sentences, para_chunk.id)

                for sent_chunk in sent_chunks:
                    self.chunks.append(sent_chunk)
                    self.chunk_lookup[sent_chunk.id] = sent_chunk
                    para_chunk.children_ids.append(sent_chunk.id)

        return self.chunks

    def _create_plain_paragraphs(self, paragraphs: List[Dict], parent_id: str) -> List[Chunk]:
        """No overlap paragraphs"""
        chunks = []
        for para_data in paragraphs:
            para_id = f"{self.doc_id}_para_{len([c for c in self.chunks if c.level == 'paragraph'])}"
            chunk = Chunk(
                id=para_id,
                content=para_data['content'],
                level="paragraph",
                parent_id=parent_id,
                metadata={
                    "core_content": para_data['content'],
                    "paragraph_index": para_data['paragraph_index'],
                    "word_count": len(para_data['content'].split()),
                    "retrievable": True
                }
            )
            chunks.append(chunk)
        return chunks

    def _create_plain_sentences(self, sentences: List[Dict], parent_id: str) -> List[Chunk]:
        """No overlap sentences"""
        chunks = []
        for sent_data in sentences:
            sent_id = f"{self.doc_id}_sent_{len([c for c in self.chunks if c.level == 'sentence'])}"
            chunk = Chunk(
                id=sent_id,
                content=sent_data['content'],
                level="sentence",
                parent_id=parent_id,
                metadata={
                    "core_content": sent_data['content'],
                    "sentence_index": sent_data['sentence_index'],
                    "char_count": len(sent_data['content']),
                    "retrievable": True
                }
            )
            chunks.append(chunk)
        return chunks

    # ------------------ Fixed-size Chunking -------------------
    def _fixed_size_chunking(self, content: str) -> List[Chunk]:
        words = content.split()
        chunks = []
        for i in range(0, len(words), self.fixed_chunk_size):
            chunk_words = words[i:i+self.fixed_chunk_size]
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{self.doc_id}_fixed_{i//self.fixed_chunk_size}"
            chunk = Chunk(
                id=chunk_id,
                content=chunk_text,
                level="fixed",
                parent_id=None,
                metadata={
                    "start_index": i,
                    "end_index": i+len(chunk_words),
                    "word_count": len(chunk_words),
                    "retrievable": True
                }
            )
            chunks.append(chunk)
        self.chunks.extend(chunks)
        return chunks
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
    # ------------------ Reuse existing helpers -------------------
    def _detect_sections(self, content: str) -> List[Dict]:
        section_pattern = r'(?m)^(#{1,3})\s*(.+?)\n(.*?)(?=\n#{1,3}\s*|\Z)'
        matches = list(re.finditer(section_pattern, content, re.DOTALL))
        sections = []

        first_header_start = matches[0].start() if matches else len(content)
        initial_content = content[:first_header_start].strip()
        if initial_content:
            sections.append({
                "title": "Introduction",
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

        if not sections and content.strip():
            sections.append({
                "title": self.title if self.title else "Main Content",
                "content": content,
                "level": 1
            })
        return sections

    def _detect_paragraphs(self, content: str) -> List[Dict]:
        raw_paragraphs = content.split('\n\n')
        paragraphs = []
        for i, para in enumerate(raw_paragraphs):
            para = para.strip()
            if para:
                paragraphs.append({
                    "content": para,
                    "paragraph_index": i,
                    "word_count": len(para.split())
                })
        return paragraphs

    def _detect_sentences(self, content: str) -> List[Dict]:
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
                "retrievable": False
            }
        )


# keep get_chunking_analysis from before (unchanged)
def get_chunking_analysis(chunks: List[Chunk]):
    total_chunks = len(chunks)
    retrievable_chunks = [c for c in chunks if c.metadata.get('retrievable', True)]
    total_characters = sum(len(c.content) for c in retrievable_chunks)
    avg_chunk_length = total_characters / len(retrievable_chunks) if retrievable_chunks else 0

    sample_chunks_data = []
    for chunk in retrievable_chunks[:5]:
        sample_chunks_data.append({
            "id": chunk.id,
            "level": chunk.level,
            "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "metadata": chunk.metadata
        })

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
