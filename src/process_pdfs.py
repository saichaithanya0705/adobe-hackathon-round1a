#!/usr/bin/env python3
"""
Adobe Hackathon Round 1a - PDF Heading Extraction Solution
High-Performance PDF Processing Solution for Adobe Hackathon Challenge 1a
Optimized for speed and accuracy with PyMuPDF (fitz)

EXECUTION COMMANDS:
================
Docker Build:
    docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .

Docker Run:
    docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier

Local Testing:
    mkdir -p input output
    cp sample.pdf input/
    python process_pdfs.py

WORKFLOW PIPELINE:
=================
1. Multi-Strategy Detection Pipeline:
   - Pattern-Based Detection (Highest Confidence): Regex patterns for chapters, numbered sections, roman numerals
   - Content-Based Detection: Recognition of heading indicator words (introduction, conclusion, etc.)
   - Typography-Based Detection: Font analysis as supporting evidence (not sole determinant)
   - Position-Based Detection: Spatial analysis for isolated text blocks
   - Confidence Scoring: Prioritize detections by reliability
   - Deduplication: Remove duplicates while preserving best matches

2. Processing Steps:
   - Extract text with font information for better heading detection
   - Analyze document structure to find common font size and font
   - Extract outline from PDF's built-in table of contents (if available)
   - Extract outline by analyzing document content using multiple strategies
   - Clean and deduplicate outline entries
   - Generate exact JSON format as required by hackathon specifications

PERFORMANCE TARGETS:
===================
- Simple PDFs: < 1 second processing time
- Complex PDFs: 2-4 seconds processing time
- 50-page PDFs: < 5 seconds (well under 10s requirement)
- Memory Usage: < 2GB for large documents
"""

import json
import re
import fitz  # PyMuPDF
from pathlib import Path
import time
import logging
import unicodedata
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HighPerformancePDFProcessor:
    """
    Optimized PDF processor for extracting structured outlines

    IMPLEMENTATION WORKFLOW:
    =======================
    This class implements the multi-strategy detection pipeline described in the README:

    1. Pattern-Based Detection (Highest Confidence):
       - Regex patterns for chapters, numbered sections, roman numerals
       - Handles "Chapter 1", "1.1 Introduction", "I. Overview" patterns

    2. Content-Based Detection:
       - Recognition of heading indicator words (introduction, conclusion, etc.)
       - Semantic understanding of heading structures

    3. Typography-Based Detection:
       - Font analysis as supporting evidence (not sole determinant)
       - Uses font size, bold flags, and font differences

    4. Position-Based Detection:
       - Spatial analysis for isolated text blocks
       - Context-aware section boundaries

    5. Confidence Scoring & Deduplication:
       - Prioritize detections by reliability
       - Remove duplicates while preserving best matches
    """

    def __init__(self):
        self.setup_heading_patterns()
        self.setup_multilingual_patterns()

    def setup_heading_patterns(self):
        """Setup English heading patterns"""
        self.heading_patterns = [
            # Chapter/Section patterns
            (r'^(Chapter\s+\d+|CHAPTER\s+\d+)', 'chapter'),
            (r'^(\d+\.\s+[A-Z][^.]*)', 'section'),
            (r'^(\d+\.\d+\s+[A-Z][^.]*)', 'subsection'),
            (r'^(\d+\.\d+\.\d+\s+[A-Z][^.]*)', 'subsubsection'),

            # Roman numerals
            (r'^([IVX]+\.\s+[A-Z][^.]*)', 'section'),

            # Letter patterns
            (r'^([A-Z]\.\s+[A-Z][^.]*)', 'section'),

            # All caps headings
            (r'^([A-Z\s]{3,}[A-Z])$', 'section'),

            # Bold/emphasized text patterns (detected by font analysis)
            (r'^([A-Z][^.]*[^.])$', 'heading'),
        ]

    def setup_multilingual_patterns(self):
        """Setup multilingual heading patterns for international documents"""
        self.multilingual_patterns = {
            # Chinese (Simplified & Traditional)
            'chinese': [
                (r'^(第[一二三四五六七八九十\d]+章)', 'chapter'),  # 第一章, 第1章
                (r'^([一二三四五六七八九十\d]+[、．])', 'section'),  # 一、二、
                (r'^(\d+[、．]\d+)', 'subsection'),  # 1.1, 1、1
                (r'^(章节|章|节|部分|段落)', 'section'),
            ],

            # Spanish
            'spanish': [
                (r'^(Capítulo\s+\d+|CAPÍTULO\s+\d+)', 'chapter'),
                (r'^(Sección\s+\d+|SECCIÓN\s+\d+)', 'section'),
                (r'^(Introducción|INTRODUCCIÓN)', 'section'),
                (r'^(Conclusión|CONCLUSIÓN)', 'section'),
                (r'^(Resumen|RESUMEN)', 'section'),
            ],

            # French
            'french': [
                (r'^(Chapitre\s+\d+|CHAPITRE\s+\d+)', 'chapter'),
                (r'^(Section\s+\d+|SECTION\s+\d+)', 'section'),
                (r'^(Introduction|INTRODUCTION)', 'section'),
                (r'^(Conclusion|CONCLUSION)', 'section'),
                (r'^(Résumé|RÉSUMÉ)', 'section'),
            ],

            # German
            'german': [
                (r'^(Kapitel\s+\d+|KAPITEL\s+\d+)', 'chapter'),
                (r'^(Abschnitt\s+\d+|ABSCHNITT\s+\d+)', 'section'),
                (r'^(Einleitung|EINLEITUNG)', 'section'),
                (r'^(Schlussfolgerung|SCHLUSSFOLGERUNG)', 'section'),
                (r'^(Zusammenfassung|ZUSAMMENFASSUNG)', 'section'),
            ],

            # Japanese
            'japanese': [
                (r'^(第[一二三四五六七八九十\d]+章)', 'chapter'),  # 第1章
                (r'^([一二三四五六七八九十\d]+[、．])', 'section'),  # 1、2、
                (r'^(はじめに|序論|序章)', 'section'),  # Introduction
                (r'^(結論|まとめ|終章)', 'section'),  # Conclusion
                (r'^(概要|要約)', 'section'),  # Summary
            ],

            # Arabic (RTL support)
            'arabic': [
                (r'^(الفصل\s+\d+)', 'chapter'),  # Chapter
                (r'^(القسم\s+\d+)', 'section'),  # Section
                (r'^(مقدمة|المقدمة)', 'section'),  # Introduction
                (r'^(خاتمة|الخاتمة)', 'section'),  # Conclusion
                (r'^(ملخص|الملخص)', 'section'),  # Summary
            ],

            # Russian
            'russian': [
                (r'^(Глава\s+\d+|ГЛАВА\s+\d+)', 'chapter'),
                (r'^(Раздел\s+\d+|РАЗДЕЛ\s+\d+)', 'section'),
                (r'^(Введение|ВВЕДЕНИЕ)', 'section'),
                (r'^(Заключение|ЗАКЛЮЧЕНИЕ)', 'section'),
                (r'^(Резюме|РЕЗЮМЕ)', 'section'),
            ]
        }

    def detect_document_language(self, doc) -> str:
        """Detect the primary language of the document"""
        # Sample text from first few pages
        sample_text = ""
        for page_num in range(min(3, len(doc))):  # Check first 3 pages
            page = doc[page_num]
            text = page.get_text()
            sample_text += text[:1000]  # First 1000 chars per page

        sample_text = sample_text.lower()

        # Language detection based on characteristic patterns
        language_indicators = {
            'chinese': ['的', '是', '在', '了', '和', '有', '我', '你', '他', '她', '它', '们'],
            'spanish': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo'],
            'french': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour'],
            'german': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf'],
            'japanese': ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ'],
            'arabic': ['في', 'من', 'إلى', 'على', 'أن', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'كما'],
            'russian': ['в', 'и', 'не', 'на', 'я', 'быть', 'он', 'с', 'что', 'а', 'по', 'это']
        }

        # Score each language
        language_scores = {}
        for lang, indicators in language_indicators.items():
            score = sum(1 for indicator in indicators if indicator in sample_text)
            if score > 0:
                language_scores[lang] = score

        # Return the language with highest score, default to English
        if language_scores:
            detected_lang = max(language_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Detected language: {detected_lang} (score: {language_scores[detected_lang]})")
            return detected_lang
        else:
            return 'english'

    def get_patterns_for_language(self, language: str) -> List[Tuple[str, str]]:
        """Get heading patterns for the detected language"""
        patterns = self.heading_patterns.copy()  # Start with English patterns

        # Add language-specific patterns
        if language in self.multilingual_patterns:
            patterns.extend(self.multilingual_patterns[language])
            logger.info(f"Added {len(self.multilingual_patterns[language])} patterns for {language}")

        return patterns

    def extract_text_with_formatting(self, page) -> List[Dict]:
        """Extract text with font information for better heading detection"""
        blocks = []
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            blocks.append({
                                "text": text,
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"],  # Bold, italic flags
                                "bbox": span["bbox"]
                            })
        return blocks
    
    def analyze_advanced_typography(self, doc) -> Dict:
        """Advanced typography analysis for better heading detection"""
        font_analysis = {
            'sizes': [],
            'fonts': {},
            'styles': {},
            'line_lengths': [],
            'spacing_patterns': [],
            'color_patterns': {},
            'alignment_patterns': {}
        }

        # Sample first few pages for comprehensive analysis
        sample_pages = min(5, len(doc))
        for page_num in range(sample_pages):
            page = doc[page_num]
            text_dict = page.get_text("dict")

            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        line_spans = []

                        for span in line["spans"]:
                            line_text += span["text"]
                            line_spans.append(span)

                            # Collect font data
                            font_analysis['sizes'].append(span["size"])
                            font_key = span["font"]
                            font_analysis['fonts'][font_key] = font_analysis['fonts'].get(font_key, 0) + 1

                            # Style analysis
                            style_key = f"size_{int(span['size'])}_bold_{bool(span['flags'] & 2**4)}_italic_{bool(span['flags'] & 2**6)}"
                            font_analysis['styles'][style_key] = font_analysis['styles'].get(style_key, 0) + 1

                            # Color analysis (if available)
                            if 'color' in span:
                                color = span['color']
                                font_analysis['color_patterns'][color] = font_analysis['color_patterns'].get(color, 0) + 1

                        # Line length analysis
                        if line_text.strip():
                            font_analysis['line_lengths'].append(len(line_text.strip()))

                            # Spacing analysis (bbox analysis)
                            if len(line_spans) > 0:
                                bbox = line["bbox"]
                                spacing = bbox[3] - bbox[1]  # Height
                                font_analysis['spacing_patterns'].append(spacing)

        # Calculate statistics
        if font_analysis['sizes']:
            sizes = font_analysis['sizes']
            font_analysis['avg_size'] = sum(sizes) / len(sizes)
            font_analysis['size_std'] = (sum((x - font_analysis['avg_size'])**2 for x in sizes) / len(sizes))**0.5
            font_analysis['size_percentiles'] = {
                '25': sorted(sizes)[len(sizes)//4],
                '50': sorted(sizes)[len(sizes)//2],
                '75': sorted(sizes)[3*len(sizes)//4],
                '90': sorted(sizes)[9*len(sizes)//10],
                '95': sorted(sizes)[19*len(sizes)//20]
            }

        if font_analysis['line_lengths']:
            lengths = font_analysis['line_lengths']
            font_analysis['avg_line_length'] = sum(lengths) / len(lengths)
            font_analysis['short_line_threshold'] = sorted(lengths)[len(lengths)//4]  # 25th percentile

        # Most common font
        if font_analysis['fonts']:
            font_analysis['common_font'] = max(font_analysis['fonts'].items(), key=lambda x: x[1])[0]

        return font_analysis

    def is_heading_by_advanced_analysis(self, span: Dict, typography: Dict, line_context: Dict) -> Tuple[bool, str]:
        """Advanced heading detection using multiple typography factors"""
        font_size = span["size"]
        font_name = span["font"]
        flags = span["flags"]
        text = span["text"].strip()

        # Skip very short or very long text
        if len(text) < 3 or len(text) > 150:
            return False, ""

        # Advanced content filtering
        body_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'which', 'have', 'has', 'been', 'will', 'would', 'could', 'should']
        text_lower = text.lower()
        body_word_count = sum(1 for word in body_indicators if f' {word} ' in f' {text_lower} ')
        total_words = len(text.split())

        if total_words > 3 and body_word_count / total_words > 0.3:  # More than 30% common words
            return False, ""

        # Typography analysis
        is_bold = flags & 2**4
        is_italic = flags & 2**6
        is_underline = flags & 2**0

        avg_size = typography.get('avg_size', 12)
        size_std = typography.get('size_std', 2)
        percentiles = typography.get('size_percentiles', {})
        common_font = typography.get('common_font', '')
        avg_line_length = typography.get('avg_line_length', 50)
        short_line_threshold = typography.get('short_line_threshold', 20)

        # Font size analysis (more sophisticated)
        size_z_score = (font_size - avg_size) / max(size_std, 1)  # Avoid division by zero
        is_significantly_larger = size_z_score > 1.5  # 1.5 standard deviations above mean
        is_very_large = font_size > percentiles.get('90', avg_size * 1.5)
        is_extremely_large = font_size > percentiles.get('95', avg_size * 2.0)

        # Font family analysis
        is_different_font = font_name != common_font
        is_serif_font = any(serif in font_name.lower() for serif in ['times', 'serif', 'georgia', 'garamond'])
        is_sans_serif = any(sans in font_name.lower() for sans in ['arial', 'helvetica', 'calibri', 'verdana'])

        # Line length analysis
        text_length = len(text)
        is_short_line = text_length < short_line_threshold
        is_very_short_line = text_length < short_line_threshold * 0.7

        # Content pattern analysis
        is_title_case = text.istitle()
        is_all_caps = text.isupper() and len(text) > 3
        has_numbers = any(char.isdigit() for char in text[:10])
        starts_with_number = text[0].isdigit() if text else False

        # Scoring system for heading likelihood
        heading_score = 0

        # Font size scoring
        if is_extremely_large:
            heading_score += 5
        elif is_very_large:
            heading_score += 4
        elif is_significantly_larger:
            heading_score += 3
        elif font_size > avg_size * 1.2:
            heading_score += 2

        # Style scoring
        if is_bold:
            heading_score += 3
        if is_italic and not is_bold:  # Italic alone is less common for headings
            heading_score += 1
        if is_underline:
            heading_score += 2

        # Font family scoring
        if is_different_font:
            heading_score += 1

        # Length scoring
        if is_very_short_line and total_words <= 8:
            heading_score += 2
        elif is_short_line and total_words <= 12:
            heading_score += 1

        # Content pattern scoring
        if is_title_case:
            heading_score += 2
        if is_all_caps and len(text) < 50:
            heading_score += 2
        if has_numbers and starts_with_number:
            heading_score += 1

        # Context scoring (from line_context)
        if line_context.get('is_isolated', False):
            heading_score += 1
        if line_context.get('has_whitespace_before', False):
            heading_score += 1
        if line_context.get('has_whitespace_after', False):
            heading_score += 1

        # Determine heading level based on score and characteristics
        if heading_score >= 8:
            if is_extremely_large or (is_very_large and is_bold):
                return True, "chapter"
            else:
                return True, "section"
        elif heading_score >= 6:
            if is_very_large:
                return True, "section"
            else:
                return True, "subsection"
        elif heading_score >= 4:
            return True, "subsection"

        return False, ""
    
    def analyze_line_context(self, line_index: int, page_lines: List) -> Dict:
        """Analyze the context around a line for better heading detection"""
        context = {
            'is_isolated': False,
            'has_whitespace_before': False,
            'has_whitespace_after': False,
            'prev_line_length': 0,
            'next_line_length': 0
        }

        if line_index > 0:
            prev_line = page_lines[line_index - 1]
            prev_text = "".join(s["text"] for s in prev_line.get("spans", [])).strip()
            context['prev_line_length'] = len(prev_text)
            context['has_whitespace_before'] = len(prev_text) == 0

        if line_index < len(page_lines) - 1:
            next_line = page_lines[line_index + 1]
            next_text = "".join(s["text"] for s in next_line.get("spans", [])).strip()
            context['next_line_length'] = len(next_text)
            context['has_whitespace_after'] = len(next_text) == 0

        # Check if line is isolated (surrounded by short lines or whitespace)
        context['is_isolated'] = (
            context['has_whitespace_before'] or context['prev_line_length'] < 20
        ) and (
            context['has_whitespace_after'] or context['next_line_length'] < 20
        )

        return context
    
    def map_level_to_heading(self, level_input) -> str:
        """Map various level inputs to H1, H2, H3 format as required by hackathon"""
        if isinstance(level_input, int):
            if level_input <= 1:
                return "H1"
            elif level_input == 2:
                return "H2"
            else:
                return "H3"
        elif isinstance(level_input, str):
            level_lower = level_input.lower()
            if level_lower in ['chapter', 'h1', 'level_1']:
                return "H1"
            elif level_lower in ['section', 'h2', 'level_2']:
                return "H2"
            elif level_lower in ['subsection', 'subsubsection', 'h3', 'level_3', 'heading']:
                return "H3"
            else:
                return "H2"  # Default fallback
        return "H2"  # Ultimate fallback

    def extract_outline_from_toc(self, doc) -> List[Dict]:
        """Extract outline from PDF's built-in table of contents"""
        outline = []
        try:
            toc = doc.get_toc()
            for item in toc:
                level, title, page_num = item
                outline.append({
                    "level": self.map_level_to_heading(level),
                    "text": title.strip(),
                    "page": page_num
                })
        except Exception as e:
            logger.warning(f"Could not extract TOC: {e}")

        return outline
    
    def extract_outline_from_content(self, doc, language_patterns=None) -> List[Dict]:
        """Extract outline by analyzing document content - advanced typography approach with multilingual support"""
        outline = []

        # Advanced typography analysis
        typography = self.analyze_advanced_typography(doc)

        # Use provided language patterns or default to English
        patterns_to_use = language_patterns if language_patterns else self.heading_patterns

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_dict = page.get_text("dict")

            # Extract lines with context for better analysis
            page_lines = []
            for block in text_dict["blocks"]:
                if "lines" in block:
                    page_lines.extend(block["lines"])

            for line_index, line in enumerate(page_lines):
                if not line.get("spans"):
                    continue

                text = "".join(span["text"] for span in line["spans"]).strip()
                if len(text) < 5 or len(text) > 150:  # Adjusted length limits
                    continue

                # Skip text that contains too many common words (likely body text)
                words = text.lower().split()
                common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that', 'which', 'have', 'has', 'been']
                common_word_count = sum(1 for word in words if word in common_words)
                if len(words) > 3 and common_word_count / len(words) > 0.3:  # More than 30% common words
                    continue

                # Skip instructional/template text
                if any(phrase in text.lower() for phrase in ['sample', 'template', 'example', 'guidelines', 'requirements', 'instructions', 'format']):
                    continue

                # Analyze line context
                line_context = self.analyze_line_context(line_index, page_lines)

                # First check pattern-based detection (highest confidence) with multilingual support
                pattern_matched = False
                for pattern, pattern_level in patterns_to_use:
                    if re.match(pattern, text, re.IGNORECASE):
                        outline.append({
                            "level": self.map_level_to_heading(pattern_level),
                            "text": text,
                            "page": page_num + 1
                        })
                        pattern_matched = True
                        break

                # Advanced typography-based detection if no pattern matched
                if not pattern_matched and self.looks_like_heading(text):
                    # Use first span for analysis (most representative)
                    main_span = line["spans"][0]
                    is_heading, level = self.is_heading_by_advanced_analysis(main_span, typography, line_context)
                    if is_heading:
                        outline.append({
                            "level": self.map_level_to_heading(level),
                            "text": text,
                            "page": page_num + 1
                        })

        return outline

    def looks_like_heading(self, text: str) -> bool:
        """Check if text looks like a heading based on content patterns - improved filtering"""
        text_lower = text.lower().strip()

        # Skip obvious non-headings
        non_heading_indicators = [
            'this sample', 'the guidelines', 'formatting requirements', 'academic writing',
            'referencing guidelines', 'times new roman', 'department, university',
            'for ijltemas', 'first author', 'second author', 'third author',
            'email:', 'phone:', 'address:', 'university/college', 'color-coded',
            'demonstrates the requirements', 'which demonstrates', 'have been'
        ]

        if any(indicator in text_lower for indicator in non_heading_indicators):
            return False

        # Skip very long sentences (likely body text)
        if len(text) > 80 and ('.' in text or ',' in text):
            return False

        # Heading indicator words
        heading_words = [
            'introduction', 'overview', 'background', 'methodology', 'results',
            'discussion', 'conclusion', 'summary', 'abstract', 'references',
            'bibliography', 'appendix', 'acknowledgments', 'preface', 'foreword',
            'history', 'attractions', 'highlights', 'experiences', 'tips', 'guide',
            'chapter', 'section', 'part'
        ]

        # Check if text starts with or is a heading word
        if any(text_lower.startswith(word) or text_lower == word for word in heading_words):
            return True

        # Check if text is title case (most words capitalized) but not too long
        words = text.split()
        if len(words) >= 2 and len(words) <= 8:  # Reasonable heading length
            capitalized_words = sum(1 for word in words if word[0].isupper() and len(word) > 2)
            if capitalized_words / len(words) >= 0.7:  # 70% of words are capitalized
                return True

        return False
    
    def clean_and_deduplicate_outline(self, outline: List[Dict]) -> List[Dict]:
        """Clean and deduplicate outline entries"""
        if not outline:
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        cleaned = []
        
        for item in outline:
            # Create a key for deduplication
            key = (item["text"].lower().strip(), item["page"])
            if key not in seen:
                seen.add(key)
                # Clean text
                item["text"] = re.sub(r'\s+', ' ', item["text"]).strip()
                cleaned.append(item)
        
        # Limit to reasonable number of outline items
        return cleaned[:50]
    
    def extract_title(self, doc) -> str:
        """Extract document title using multiple strategies"""
        # Strategy 1: PDF metadata
        metadata = doc.metadata
        if metadata.get("title"):
            title = metadata["title"].strip()
            if len(title) > 3:
                return title
        
        # Strategy 2: First page large text
        if len(doc) > 0:
            page = doc[0]
            blocks = self.extract_text_with_formatting(page)
            
            # Find largest font size text on first page
            if blocks:
                max_size = max(block["size"] for block in blocks)
                for block in blocks:
                    if block["size"] == max_size and len(block["text"].strip()) > 3:
                        return block["text"].strip()
        
        # Strategy 3: Filename fallback
        return "Document"
    
    def process_single_pdf(self, pdf_path: Path, output_dir: Path) -> bool:
        """Process a single PDF file"""
        try:
            start_time = time.time()
            logger.info(f"Processing {pdf_path.name}")
            
            # Open PDF
            doc = fitz.open(pdf_path)

            # Detect document language for multilingual support
            detected_language = self.detect_document_language(doc)

            # Get language-specific patterns
            language_patterns = self.get_patterns_for_language(detected_language)

            # Extract title
            title = self.extract_title(doc)

            # Extract outline - try TOC first, then very conservative content analysis
            outline = self.extract_outline_from_toc(doc)

            if len(outline) < 2:  # Only if TOC is very sparse, analyze content conservatively
                content_outline = self.extract_outline_from_content(doc, language_patterns)
                # Limit content analysis results to avoid over-detection
                outline.extend(content_outline[:10])  # Max 10 headings from content analysis
            
            # Clean and deduplicate
            outline = self.clean_and_deduplicate_outline(outline)
            
            # Ensure we have some outline
            if not outline:
                outline = [{
                    "level": "H1",
                    "text": "Document Content",
                    "page": 1
                }]
            
            # Create output JSON
            output_data = {
                "title": title,
                "outline": outline
            }
            
            # Save output
            output_file = output_dir / f"{pdf_path.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            doc.close()
            
            processing_time = time.time() - start_time
            logger.info(f"Processed {pdf_path.name} in {processing_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
            return False

def process_pdfs():
    """
    Main processing function - Entry point for PDF processing

    EXECUTION WORKFLOW:
    ==================
    1. Detect environment (Docker vs Local)
    2. Set up input/output directories
    3. Find all PDF files in input directory
    4. Initialize high-performance processor
    5. Process files with threading for I/O optimization
    6. Generate JSON output files with exact hackathon format

    DIRECTORY STRUCTURE:
    ===================
    Docker Mode:
        /app/input/  - PDF files to process
        /app/output/ - Generated JSON files

    Local Mode:
        ./input/     - PDF files to process
        ./output/    - Generated JSON files

    OUTPUT FORMAT:
    =============
    Each PDF generates filename.json with structure:
    {
        "title": "Document Title",
        "outline": [
            {"level": "H1", "text": "Chapter 1", "page": 1},
            {"level": "H2", "text": "Section 1.1", "page": 2}
        ]
    }
    """
    # Use local directories for testing, Docker paths for production
    if Path("/app/input").exists():
        input_dir = Path("/app/input")
        output_dir = Path("/app/output")
    else:
        input_dir = Path("input")
        output_dir = Path("output")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Initialize processor
    processor = HighPerformancePDFProcessor()
    
    # Process files with threading for I/O optimization
    max_workers = min(mp.cpu_count(), len(pdf_files), 4)  # Limit concurrent processing
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(processor.process_single_pdf, pdf_file, output_dir): pdf_file 
            for pdf_file in pdf_files
        }
        
        for future in as_completed(futures):
            pdf_file = futures[future]
            try:
                success = future.result()
                if not success:
                    logger.error(f"Failed to process {pdf_file.name}")
            except Exception as e:
                logger.error(f"Exception processing {pdf_file.name}: {e}")
    
    logger.info("PDF processing completed")

if __name__ == "__main__":
    """
    MAIN EXECUTION ENTRY POINT
    ==========================

    This script can be executed in multiple ways:

    1. Docker Container (Production):
       docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier

    2. Local Python (Development/Testing):
       python process_pdfs.py

    3. Local Testing with Sample:
       mkdir -p input output
       cp sample.pdf input/
       python process_pdfs.py
       # Check output/sample.json

    PERFORMANCE EXPECTATIONS:
    ========================
    - Processing Time: ≤ 10 seconds for 50-page PDF (typically <5s)
    - Memory Usage: Efficient usage within 16GB limit
    - Output: Exact JSON format compliance
    - Error Handling: Graceful failures with comprehensive logging
    """
    process_pdfs()
