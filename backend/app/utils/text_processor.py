"""Text processing and chunking utilities."""

from typing import List, Optional
import re
import tiktoken
import structlog

logger = structlog.get_logger(__name__)


class TextProcessor:
    """Service for processing and chunking text."""

    def __init__(self, encoding_model: str = "cl100k_base"):
        """
        Initialize text processor.

        Args:
            encoding_model: The tiktoken encoding model to use.
        """
        self.encoding = tiktoken.get_encoding(encoding_model)

    def create_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        Create overlapping chunks from text.

        Args:
            text: The text to chunk.
            chunk_size: Maximum tokens per chunk.
            chunk_overlap: Number of overlapping tokens between chunks.

        Returns:
            List of text chunks.
        """
        if not text:
            return []

        # Clean and normalize text
        text = self.clean_text(text)

        # Split into sentences first for better chunk boundaries
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))

            # If single sentence is too long, split it
            if sentence_tokens > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence into smaller parts
                sub_chunks = self._split_long_sentence(sentence, chunk_size)
                chunks.extend(sub_chunks)
                continue

            # Check if adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                    # Keep overlap
                    if chunk_overlap > 0:
                        overlap_chunk = []
                        overlap_tokens = 0
                        for s in reversed(current_chunk):
                            s_tokens = len(self.encoding.encode(s))
                            if overlap_tokens + s_tokens <= chunk_overlap:
                                overlap_chunk.insert(0, s)
                                overlap_tokens += s_tokens
                            else:
                                break
                        current_chunk = overlap_chunk
                        current_tokens = overlap_tokens
                    else:
                        current_chunk = []
                        current_tokens = 0

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        logger.info("Created text chunks",
                   original_length=len(text),
                   num_chunks=len(chunks),
                   chunk_size=chunk_size,
                   overlap=chunk_overlap)

        return chunks

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text to clean.

        Returns:
            Cleaned text.
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Normalize Unicode
        text = text.encode('utf-8', errors='ignore').decode('utf-8')

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: The text to split.

        Returns:
            List of sentences.
        """
        # Simple sentence splitting
        # In production, consider using NLTK or spaCy for better accuracy
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _split_long_sentence(self, sentence: str, max_tokens: int) -> List[str]:
        """
        Split a long sentence into smaller chunks.

        Args:
            sentence: The sentence to split.
            max_tokens: Maximum tokens per chunk.

        Returns:
            List of sentence chunks.
        """
        words = sentence.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = len(self.encoding.encode(word))

            if current_tokens + word_tokens > max_tokens:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in text.

        Args:
            text: The text to count tokens for.

        Returns:
            Number of tokens.
        """
        return len(self.encoding.encode(text))

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.

        Simple implementation - in production, consider using
        TF-IDF or other NLP techniques.

        Args:
            text: The text to extract keywords from.
            max_keywords: Maximum number of keywords to extract.

        Returns:
            List of keywords.
        """
        # Clean text
        text = self.clean_text(text.lower())

        # Remove common stop words (simplified list)
        stop_words = {
            "the", "is", "at", "which", "on", "and", "a", "an",
            "as", "are", "was", "were", "been", "be", "have",
            "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of",
            "in", "for", "with", "by", "from", "about", "into",
            "through", "during", "before", "after", "above",
            "below", "up", "down", "out", "off", "over", "under",
            "again", "further", "then", "once"
        }

        # Extract words
        words = re.findall(r'\b[a-z]+\b', text)

        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]

        return keywords

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Create a simple summary of text.

        This is a very basic implementation that just takes
        the first part of the text. In production, consider
        using more sophisticated summarization techniques.

        Args:
            text: The text to summarize.
            max_length: Maximum length of summary in characters.

        Returns:
            Text summary.
        """
        text = self.clean_text(text)

        if len(text) <= max_length:
            return text

        # Find a good breaking point
        summary = text[:max_length]
        last_period = summary.rfind('.')
        last_space = summary.rfind(' ')

        if last_period > max_length * 0.8:
            summary = summary[:last_period + 1]
        elif last_space > max_length * 0.8:
            summary = summary[:last_space] + "..."
        else:
            summary = summary + "..."

        return summary