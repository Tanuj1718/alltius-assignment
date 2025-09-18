#!/usr/bin/env python3
"""
PDF Content Extractor
=====================

A Python program that parses PDF files and extracts content into structured JSON format.
Supports extraction of paragraphs, tables, and charts while preserving hierarchical structure.

Author: Assistant
Version: 1.0
"""

import json
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber")
    exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Run: pip install PyMuPDF")
    exit(1)

try:
    import camelot
except ImportError:
    print("Warning: camelot-py not installed. Table extraction may be limited.")
    camelot = None


class PDFContentExtractor:
    """
    Main class for extracting structured content from PDF files.
    """

    def __init__(self, pdf_path: str, verbose: bool = False):
        """
        Initialize the PDF extractor.

        Args:
            pdf_path (str): Path to the PDF file
            verbose (bool): Enable verbose logging
        """
        self.pdf_path = Path(pdf_path)
        self.verbose = verbose
        self.setup_logging()

        # Section detection patterns
        self.section_patterns = [
            r'^\s*([A-Z][A-Za-z\s]+)\s*$',  # All caps or title case headings
            r'^\s*\d+\.\s+([A-Za-z][A-Za-z\s]+)\s*$',  # Numbered sections
            r'^\s*([A-Z]+[A-Z\s]*[A-Z]+)\s*$',  # ALL CAPS sections
            r'^\s*Chapter\s+\d+[:\.]?\s*([A-Za-z][A-Za-z\s]+)\s*$',  # Chapter headings
        ]

        self.subsection_patterns = [
            r'^\s*\d+\.\d+\.?\s+([A-Za-z][A-Za-z\s]+)\s*$',  # 1.1, 1.2, etc.
            r'^\s*[a-z]\)\s+([A-Za-z][A-Za-z\s]+)\s*$',  # a), b), etc.
            r'^\s*[A-Z]\)\s+([A-Za-z][A-Za-z\s]+)\s*$',  # A), B), etc.
        ]

        # Current context for hierarchical tracking
        self.current_section = None
        self.current_subsection = None

    def setup_logging(self):
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def extract_content(self) -> Dict[str, Any]:
        """
        Main method to extract all content from PDF.

        Returns:
            Dict containing structured PDF content
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        self.logger.info(f"Starting extraction from: {self.pdf_path}")

        result = {
            "metadata": {
                "source_file": str(self.pdf_path),
                "total_pages": 0,
                "extraction_timestamp": "",
            },
            "pages": []
        }

        # Extract content using pdfplumber
        with pdfplumber.open(self.pdf_path) as pdf:
            result["metadata"]["total_pages"] = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, 1):
                self.logger.debug(f"Processing page {page_num}")
                page_content = self.extract_page_content(page, page_num)
                result["pages"].append(page_content)

        # Add charts/images using PyMuPDF
        self.extract_charts_and_images(result)

        # Add timestamp
        from datetime import datetime
        result["metadata"]["extraction_timestamp"] = datetime.now().isoformat()

        self.logger.info("Extraction completed successfully")
        return result

    def extract_page_content(self, page, page_num: int) -> Dict[str, Any]:
        """
        Extract content from a single page.

        Args:
            page: pdfplumber page object
            page_num (int): Page number

        Returns:
            Dict containing page content
        """
        page_data = {
            "page_number": page_num,
            "content": []
        }

        # Extract tables first
        tables = self.extract_tables(page, page_num)

        # Extract text content
        text_content = self.extract_text_content(page, page_num, tables)

        # Combine and sort by position
        all_content = tables + text_content

        # Sort by approximate vertical position
        all_content.sort(key=lambda x: x.get('_position', 0))

        # Remove temporary position markers
        for item in all_content:
            item.pop('_position', None)

        page_data["content"] = all_content
        return page_data

    def extract_tables(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract tables from a page.

        Args:
            page: pdfplumber page object
            page_num (int): Page number

        Returns:
            List of table dictionaries
        """
        tables = []

        try:
            # Extract tables using pdfplumber
            page_tables = page.extract_tables()

            for i, table_data in enumerate(page_tables):
                if table_data and len(table_data) > 1:  # Must have header + data
                    table_dict = {
                        "type": "table",
                        "section": self.current_section,
                        "sub_section": self.current_subsection,
                        "description": f"Table {i+1} from page {page_num}",
                        "table_data": self.clean_table_data(table_data),
                        "_position": self.get_table_position(page, i)
                    }
                    tables.append(table_dict)
                    self.logger.debug(f"Extracted table {i+1} from page {page_num}")

        except Exception as e:
            self.logger.warning(f"Error extracting tables from page {page_num}: {e}")

        # Try camelot for better table extraction if available
        if camelot and len(tables) == 0:
            try:
                camelot_tables = camelot.read_pdf(str(self.pdf_path), pages=str(page_num))
                for i, table in enumerate(camelot_tables):
                    if not table.df.empty:
                        table_data = table.df.values.tolist()
                        headers = table.df.columns.tolist()
                        full_table = [headers] + table_data

                        table_dict = {
                            "type": "table",
                            "section": self.current_section,
                            "sub_section": self.current_subsection,
                            "description": f"Table {i+1} from page {page_num} (camelot)",
                            "table_data": self.clean_table_data(full_table),
                            "_position": 300  # Approximate middle position
                        }
                        tables.append(table_dict)

            except Exception as e:
                self.logger.debug(f"Camelot extraction failed for page {page_num}: {e}")

        return tables

    def extract_text_content(self, page, page_num: int, existing_tables: List) -> List[Dict[str, Any]]:
        """
        Extract text content from a page.

        Args:
            page: pdfplumber page object
            page_num (int): Page number
            existing_tables (List): Already extracted tables to avoid duplication

        Returns:
            List of text content dictionaries
        """
        content = []

        try:
            # Extract text
            text = page.extract_text()
            if not text:
                return content

            # Split into lines and process
            lines = text.split('\n')
            current_paragraph = []

            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    # Empty line - end current paragraph
                    if current_paragraph:
                        content.append(self.create_paragraph_dict(
                            ' '.join(current_paragraph), 
                            page_num, 
                            line_num
                        ))
                        current_paragraph = []
                    continue

                # Check if line is a section/subsection heading
                section_match = self.detect_section(line)
                subsection_match = self.detect_subsection(line)

                if section_match:
                    # Save current paragraph if exists
                    if current_paragraph:
                        content.append(self.create_paragraph_dict(
                            ' '.join(current_paragraph), 
                            page_num, 
                            line_num
                        ))
                        current_paragraph = []

                    self.current_section = section_match
                    self.current_subsection = None
                    self.logger.debug(f"Found section: {section_match}")
                    continue

                elif subsection_match:
                    # Save current paragraph if exists
                    if current_paragraph:
                        content.append(self.create_paragraph_dict(
                            ' '.join(current_paragraph), 
                            page_num, 
                            line_num
                        ))
                        current_paragraph = []

                    self.current_subsection = subsection_match
                    self.logger.debug(f"Found subsection: {subsection_match}")
                    continue

                # Regular text line
                current_paragraph.append(line)

            # Add final paragraph if exists
            if current_paragraph:
                content.append(self.create_paragraph_dict(
                    ' '.join(current_paragraph), 
                    page_num, 
                    len(lines)
                ))

        except Exception as e:
            self.logger.warning(f"Error extracting text from page {page_num}: {e}")

        return content

    def extract_charts_and_images(self, result: Dict[str, Any]):
        """
        Extract charts and images using PyMuPDF.

        Args:
            result (Dict): The result dictionary to update
        """
        try:
            doc = fitz.open(self.pdf_path)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()

                if image_list:
                    page_content = result["pages"][page_num]["content"]

                    for img_index, img in enumerate(image_list):
                        # Get image info
                        xref = img[0]
                        try:
                            base_image = doc.extract_image(xref)
                            image_data = base_image["image"]

                            # Create chart entry
                            chart_dict = {
                                "type": "chart",
                                "section": self.current_section,
                                "sub_section": self.current_subsection,
                                "description": f"Image/Chart {img_index + 1} from page {page_num + 1}",
                                "image_info": {
                                    "width": base_image["width"],
                                    "height": base_image["height"],
                                    "ext": base_image["ext"],
                                    "size": len(image_data)
                                },
                                "table_data": None  # Would need OCR or manual processing for chart data
                            }

                            page_content.append(chart_dict)
                            self.logger.debug(f"Found image/chart on page {page_num + 1}")

                        except Exception as e:
                            self.logger.debug(f"Could not extract image {img_index} from page {page_num + 1}: {e}")

            doc.close()

        except Exception as e:
            self.logger.warning(f"Error extracting charts/images: {e}")

    def detect_section(self, line: str) -> Optional[str]:
        """
        Detect if a line is a section heading.

        Args:
            line (str): Text line to check

        Returns:
            Section name if detected, None otherwise
        """
        for pattern in self.section_patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        return None

    def detect_subsection(self, line: str) -> Optional[str]:
        """
        Detect if a line is a subsection heading.

        Args:
            line (str): Text line to check

        Returns:
            Subsection name if detected, None otherwise
        """
        for pattern in self.subsection_patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        return None

    def create_paragraph_dict(self, text: str, page_num: int, line_num: int) -> Dict[str, Any]:
        """
        Create a paragraph dictionary.

        Args:
            text (str): Paragraph text
            page_num (int): Page number
            line_num (int): Line number for positioning

        Returns:
            Paragraph dictionary
        """
        return {
            "type": "paragraph",
            "section": self.current_section,
            "sub_section": self.current_subsection,
            "text": text.strip(),
            "_position": line_num  # For sorting
        }

    def clean_table_data(self, table_data: List[List]) -> List[List[str]]:
        """
        Clean and normalize table data.

        Args:
            table_data (List[List]): Raw table data

        Returns:
            Cleaned table data
        """
        cleaned = []
        for row in table_data:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # Convert to string and clean
                    cell_str = str(cell).strip()
                    # Remove extra whitespace
                    cell_str = re.sub(r'\s+', ' ', cell_str)
                    cleaned_row.append(cell_str)
            cleaned.append(cleaned_row)
        return cleaned

    def get_table_position(self, page, table_index: int) -> float:
        """
        Get approximate position of table on page.

        Args:
            page: pdfplumber page object
            table_index (int): Index of table on page

        Returns:
            Approximate vertical position
        """
        try:
            # This is a simplified approach
            # In a more sophisticated implementation, you would use
            # the actual bounding box coordinates
            page_height = page.height
            return (table_index + 1) * (page_height / 4)  # Rough estimation
        except:
            return 300  # Default middle position

    def save_to_json(self, content: Dict[str, Any], output_path: str):
        """
        Save extracted content to JSON file.

        Args:
            content (Dict): Extracted content
            output_path (str): Output file path
        """
        output_file = Path(output_path)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

            self.logger.info(f"JSON output saved to: {output_file}")

        except Exception as e:
            self.logger.error(f"Error saving JSON file: {e}")
            raise


def main():
    """Main function to run the PDF extractor."""
    parser = argparse.ArgumentParser(
        description="Extract structured content from PDF files to JSON format"
    )
    parser.add_argument(
        "input_pdf", 
        help="Path to input PDF file"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output JSON file path (default: input_filename.json)",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set default output path if not provided
    if args.output is None:
        input_path = Path(args.input_pdf)
        args.output = input_path.with_suffix('.json')

    try:
        # Create extractor and process PDF
        extractor = PDFContentExtractor(args.input_pdf, verbose=args.verbose)
        content = extractor.extract_content()

        # Save to JSON
        extractor.save_to_json(content, args.output)

        print(f"✅ Successfully extracted content from {args.input_pdf}")
        print(f"📄 Total pages processed: {content['metadata']['total_pages']}")
        print(f"💾 Output saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
