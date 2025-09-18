# Create comprehensive README
readme_content = '''# PDF Content Extractor

A robust Python program that parses PDF files and extracts their content into well-structured JSON format. The program preserves the hierarchical organization of documents while identifying different content types such as paragraphs, tables, and charts.

## Features

- 📄 **Multi-format Support**: Extracts text, tables, and images/charts from PDF files
- 🏗️ **Hierarchical Structure**: Maintains document organization with sections and sub-sections
- 📊 **Table Detection**: Advanced table extraction using multiple libraries
- 🖼️ **Image/Chart Detection**: Identifies and catalogs visual elements
- 🔍 **Smart Section Detection**: Automatically identifies headings and organizational structure
- 📝 **Clean Output**: Produces well-formatted, readable JSON
- 🚀 **Modular Design**: Clean, extensible codebase
- 📋 **Command Line Interface**: Easy-to-use CLI with multiple options

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Option 1: Quick Installation

```bash
# Install required dependencies
pip install pdfplumber PyMuPDF camelot-py[cv] pandas

# Download the script
git clone https://github.com/Tanuj1718/alltius-assignment.git
```

### Option 2: Manual Installation

1. **Clone or download the script**:
   ```bash
   # Save the pdf_content_extractor.py file to your working directory
   ```

2. **Install core dependencies**:
   ```bash
   pip install pdfplumber PyMuPDF
   ```

3. **Install optional dependencies for enhanced table extraction**:
   ```bash
   # For better table detection
   pip install camelot-py[cv]
   
   # If you encounter issues with camelot, try:
   pip install "camelot-py[base]"
   pip install opencv-python
   pip install ghostscript
   ```

### Dependencies Explained

- **pdfplumber**: Primary PDF text and table extraction
- **PyMuPDF (fitz)**: Image and chart detection, enhanced PDF processing
- **camelot-py**: Advanced table extraction (optional but recommended)
- **pandas**: Data processing for tables
- **opencv-python**: Image processing for camelot

## Usage

### Basic Usage

```bash
# Extract content from a PDF file
python pdf_content_extractor.py input_document.pdf

# This creates input_document.json with extracted content
```

### Advanced Usage

```bash
# Specify custom output file
python pdf_content_extractor.py input.pdf -o custom_output.json

# Enable verbose logging for debugging
python pdf_content_extractor.py input.pdf -v

# Combine options
python pdf_content_extractor.py document.pdf -o extracted_content.json -v
```

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `input_pdf` | Path to input PDF file (required) | `document.pdf` |
| `-o, --output` | Output JSON file path | `-o output.json` |
| `-v, --verbose` | Enable verbose logging | `-v` |
| `-h, --help` | Show help message | `-h` |

## Output Format

The program generates a JSON file with the following structure:

```json
{
  "metadata": {
    "source_file": "path/to/input.pdf",
    "total_pages": 5,
    "extraction_timestamp": "2025-09-18T07:44:00.123456"
  },
  "pages": [
    {
      "page_number": 1,
      "content": [
        {
          "type": "paragraph",
          "section": "Introduction",
          "sub_section": "Background",
          "text": "This is extracted paragraph text..."
        },
        {
          "type": "table",
          "section": "Financial Data",
          "sub_section": null,
          "description": "Table 1 from page 1",
          "table_data": [
            ["Year", "Revenue", "Profit"],
            ["2022", "$10M", "$2M"],
            ["2023", "$12M", "$3M"]
          ]
        },
        {
          "type": "chart",
          "section": "Performance Overview",
          "sub_section": null,
          "description": "Image/Chart 1 from page 1",
          "image_info": {
            "width": 800,
            "height": 600,
            "ext": "png",
            "size": 45678
          },
          "table_data": null
        }
      ]
    }
  ]
}
```

### Content Types

1. **Paragraph**: Regular text content with section context
2. **Table**: Structured tabular data with headers and rows
3. **Chart**: Images, diagrams, or charts (metadata only)

## Examples

### Example 1: Basic Extraction

```bash
python pdf_content_extractor.py sample_report.pdf
```

Output: `sample_report.json`

### Example 2: Processing Multiple Files

```bash
# Process multiple files in a loop (bash)
for file in *.pdf; do
    python pdf_content_extractor.py "$file" -o "${file%.pdf}_extracted.json"
done
```

### Example 3: Integration in Python Script

```python
from pdf_content_extractor import PDFContentExtractor

# Create extractor instance
extractor = PDFContentExtractor("document.pdf", verbose=True)

# Extract content
content = extractor.extract_content()

# Save to JSON
extractor.save_to_json(content, "output.json")

# Access extracted data
pages = content["pages"]
for page in pages:
    print(f"Page {page['page_number']} has {len(page['content'])} content blocks")
```

## Advanced Configuration

### Section Detection Patterns

The program automatically detects sections and subsections using regex patterns. You can modify these patterns in the `PDFContentExtractor` class:

```python
# Section patterns (modify as needed)
self.section_patterns = [
    r'^\\s*([A-Z][A-Za-z\\s]+)\\s*$',  # Title case headings
    r'^\\s*\\d+\\.\\s+([A-Za-z][A-Za-z\\s]+)\\s*$',  # Numbered sections
    # Add custom patterns here
]
```

### Troubleshooting

#### Common Issues and Solutions

1. **"pdfplumber not installed" Error**:
   ```bash
   pip install pdfplumber
   ```

2. **"PyMuPDF not installed" Error**:
   ```bash
   pip install PyMuPDF
   ```

3. **Poor Table Extraction**:
   - Install camelot for better table detection:
   ```bash
   pip install camelot-py[cv]
   ```

4. **No Charts/Images Detected**:
   - Ensure PDF contains actual images (not just visual elements)
   - Check if images are embedded or just visual layout

5. **Section Detection Issues**:
   - Enable verbose mode (`-v`) to see detection logs
   - Modify section patterns for your document format

6. **Memory Issues with Large PDFs**:
   - Process large files page by page
   - Consider splitting large PDFs before processing

#### Performance Tips

- For large PDFs, run with verbose mode first to identify bottlenecks
- Camelot table extraction is slower but more accurate
- Images extraction adds processing time but provides complete document analysis

## File Structure

```
your_project/
├── pdf_content_extractor.py  # Main script
├── README.md                 # This file
├── sample_input.pdf         # Your input files
└── extracted_output.json    # Generated output
```

## Technical Details

### Architecture

The program uses a modular approach with the following components:

- **PDFContentExtractor**: Main class handling extraction logic
- **Content Type Handlers**: Separate methods for paragraphs, tables, and charts
- **Section Detection**: Regex-based hierarchical structure detection
- **Multiple Library Support**: Combines pdfplumber, PyMuPDF, and camelot strengths

### Supported PDF Features

✅ **Supported**:
- Text paragraphs
- Tables (simple and complex)
- Embedded images
- Section headings
- Multi-page documents
- Various fonts and formatting

❌ **Limitations**:
- Chart data extraction (provides metadata only)
- OCR for scanned documents
- Complex nested table structures
- Form fields and interactive elements

## Contributing

Feel free to enhance the script with:
- Additional section detection patterns
- OCR integration for scanned PDFs
- Chart data extraction using ML
- Performance optimizations
- Additional output formats

## License

This project is provided as-is for educational and development purposes.

## Version History

- **v1.0**: Initial release with core functionality
  - Text and table extraction
  - Section detection
  - Image/chart identification
  - JSON output format

---

