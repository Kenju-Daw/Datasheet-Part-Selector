"""
Standalone Docling Test

Tests Docling directly on the D38999 PDF to verify it works.
"""
import time
from pathlib import Path

# PDF file to test
PDF_PATH = Path(r"c:\Users\kjara\Documents\GitHub\Datasheet Part Selector\amphenolaerospace_D38999_IIIseriesTV-1157224.pdf")

def test_docling():
    print("=" * 60)
    print("DOCLING STANDALONE TEST")
    print("=" * 60)
    print(f"PDF: {PDF_PATH.name}")
    print(f"Size: {PDF_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    print("-" * 60)
    
    # Import Docling
    print("\n1. Importing Docling...")
    start = time.time()
    from docling.document_converter import DocumentConverter
    print(f"   Import time: {time.time() - start:.2f}s")
    
    # Create converter
    print("\n2. Creating DocumentConverter...")
    start = time.time()
    converter = DocumentConverter()
    print(f"   Init time: {time.time() - start:.2f}s")
    
    # Convert PDF
    print("\n3. Converting PDF (this may take a while)...")
    start = time.time()
    result = converter.convert(str(PDF_PATH))
    convert_time = time.time() - start
    print(f"   Convert time: {convert_time:.2f}s")
    
    # Get the document
    doc = result.document
    
    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    # Page count
    page_count = len(doc.pages) if hasattr(doc, 'pages') else 0
    print(f"Pages: {page_count}")
    
    # Tables
    tables = list(doc.tables) if hasattr(doc, 'tables') else []
    print(f"Tables found: {len(tables)}")
    
    # Text preview
    if hasattr(doc, 'export_to_markdown'):
        markdown = doc.export_to_markdown()
        print(f"Markdown length: {len(markdown)} chars")
        print("\n--- First 500 chars of markdown ---")
        print(markdown[:500])
        print("..." if len(markdown) > 500 else "")
    
    # Export to file
    backend_dir = Path(__file__).parent
    output_file = backend_dir / "parsed_results.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Docling Parse Results\n")
        f.write(f"Source: {PDF_PATH.name}\n\n")
        
        f.write("## Metadata\n")
        f.write(f"- Pages: {page_count}\n")
        f.write(f"- Tables: {len(tables)}\n\n")
        
        f.write("## Extracted Tables\n")
        for i, table in enumerate(tables):
            f.write(f"### Table {i+1}\n")
            if hasattr(table, 'export_to_dataframe'):
                df = table.export_to_dataframe()
                f.write(df.to_markdown(index=False))
            f.write("\n\n")
            
        f.write("## Extracted Text (Markdown)\n")
        if hasattr(doc, 'export_to_markdown'):
             f.write(doc.export_to_markdown())

    print(f"\n✅ Results saved to: {output_file}")
    
    return doc, tables

if __name__ == "__main__":
    test_docling()
