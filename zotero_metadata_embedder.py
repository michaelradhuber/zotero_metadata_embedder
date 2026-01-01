#!/usr/bin/env python3
"""
Fast Zotero metadata embedder - CORRECTED VERSION
Embeds Zotero metadata into PDF files using clone_from for speed
"""

import sqlite3
from pathlib import Path
from typing import Dict, Tuple
from pypdf import PdfWriter, PdfReader
import tempfile
import shutil


def get_zotero_metadata(db_path: str, storage_dir: str) -> Dict[str, Dict]:
    """
    Extract metadata from Zotero SQLite database.
    Returns dict mapping PDF paths to their metadata.
    """
    # Connect in read-only immutable mode
    conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
    cursor = conn.cursor()

    metadata_map = {}

    # Query for PDF attachments with their parent item metadata
    # i_attachment.key is the directory name (e.g., 9XWUNHR4)
    # i_parent.key is used to get metadata from the parent item
    query = """
    SELECT
        ia.path,
        i_attachment.key as attachment_key,
        i_parent.key as parent_key,
        iv_title.value as title,
        iv_doi.value as doi,
        iv_date.value as date,
        iv_journal.value as journal,
        iv_volume.value as volume,
        iv_issue.value as issue,
        iv_pages.value as pages,
        iv_publisher.value as publisher
    FROM itemAttachments ia
    JOIN items i_attachment ON ia.itemID = i_attachment.itemID
    JOIN items i_parent ON ia.parentItemID = i_parent.itemID
    LEFT JOIN itemData id_title ON i_parent.itemID = id_title.itemID
        AND id_title.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'title')
    LEFT JOIN itemDataValues iv_title ON id_title.valueID = iv_title.valueID
    LEFT JOIN itemData id_doi ON i_parent.itemID = id_doi.itemID
        AND id_doi.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'DOI')
    LEFT JOIN itemDataValues iv_doi ON id_doi.valueID = iv_doi.valueID
    LEFT JOIN itemData id_date ON i_parent.itemID = id_date.itemID
        AND id_date.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'date')
    LEFT JOIN itemDataValues iv_date ON id_date.valueID = iv_date.valueID
    LEFT JOIN itemData id_journal ON i_parent.itemID = id_journal.itemID
        AND id_journal.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'publicationTitle')
    LEFT JOIN itemDataValues iv_journal ON id_journal.valueID = iv_journal.valueID
    LEFT JOIN itemData id_volume ON i_parent.itemID = id_volume.itemID
        AND id_volume.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'volume')
    LEFT JOIN itemDataValues iv_volume ON id_volume.valueID = iv_volume.valueID
    LEFT JOIN itemData id_issue ON i_parent.itemID = id_issue.itemID
        AND id_issue.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'issue')
    LEFT JOIN itemDataValues iv_issue ON id_issue.valueID = iv_issue.valueID
    LEFT JOIN itemData id_pages ON i_parent.itemID = id_pages.itemID
        AND id_pages.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'pages')
    LEFT JOIN itemDataValues iv_pages ON id_pages.valueID = iv_pages.valueID
    LEFT JOIN itemData id_publisher ON i_parent.itemID = id_publisher.itemID
        AND id_publisher.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'publisher')
    LEFT JOIN itemDataValues iv_publisher ON id_publisher.valueID = iv_publisher.valueID
    WHERE ia.path LIKE 'storage:%'
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    storage_path = Path(storage_dir)

    for row in rows:
        path_str, attachment_key, parent_key, title, doi, date, journal, volume, issue, pages, publisher = row

        # Extract filename from storage:filename.pdf
        if path_str and path_str.startswith('storage:'):
            filename = path_str.replace('storage:', '')

            # Use attachment_key as the directory name (e.g., 9XWUNHR4)
            if attachment_key:
                full_path = storage_path / attachment_key / filename

                # Skip if file doesn't exist
                if not full_path.exists():
                    continue
            else:
                continue

            # Get authors for the parent item
            author_query = """
            SELECT ic.firstName, ic.lastName
            FROM itemCreators ici
            JOIN creators ic ON ici.creatorID = ic.creatorID
            JOIN items i ON ici.itemID = i.itemID
            WHERE i.key = ?
            ORDER BY ici.orderIndex
            """
            cursor.execute(author_query, (parent_key,))
            author_rows = cursor.fetchall()

            authors = []
            for first, last in author_rows:
                if first and last:
                    authors.append(f"{first} {last}")
                elif last:
                    authors.append(last)
                elif first:
                    authors.append(first)

            # Build metadata dict
            metadata = {}
            if title:
                metadata['Title'] = title
            if authors:
                metadata['Author'] = '; '.join(authors)
            if doi:
                metadata['DOI'] = doi
            if date:
                metadata['Date'] = date
            if journal:
                metadata['Journal'] = journal
            if volume:
                metadata['Volume'] = volume
            if issue:
                metadata['Issue'] = issue
            if pages:
                metadata['Pages'] = pages
            if publisher:
                metadata['Publisher'] = publisher

            if metadata:  # Only add if we have some metadata
                metadata_map[str(full_path)] = metadata

    conn.close()
    return metadata_map


def update_pdf_metadata_fast(pdf_path: Path, metadata: Dict) -> Tuple[bool, str]:
    """
    Fast metadata update using clone_from - doesn't copy pages to memory.
    Uses a temporary file for safety.
    """
    try:
        # Quick validation - can we read the PDF?
        with open(pdf_path, 'rb') as f:
            test_reader = PdfReader(f)
            if len(test_reader.pages) == 0:
                return False, "PDF has no pages"
            existing_meta = test_reader.metadata if test_reader.metadata else {}

        # Create writer with clone_from (efficient)
        writer = PdfWriter(clone_from=str(pdf_path))

        # Build new metadata dict - preserve existing + add new
        new_metadata = {}

        # Preserve existing metadata
        for key, value in existing_meta.items():
            new_metadata[key] = value

        # Add/update with Zotero metadata
        for key, value in metadata.items():
            # Add leading slash if not present
            pdf_key = key if key.startswith('/') else f'/{key}'
            new_metadata[pdf_key] = str(value)

        # Set metadata
        writer.metadata = new_metadata

        # Write to temp file first for safety
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', dir=pdf_path.parent)
        try:
            with open(temp_fd, 'wb') as temp_f:
                writer.write(temp_f)

            # Verify temp file
            temp_size = Path(temp_path).stat().st_size
            if temp_size < 100:
                return False, f"Temp file too small: {temp_size} bytes"

            # Quick verification
            with open(temp_path, 'rb') as verify_f:
                verify_reader = PdfReader(verify_f)
                if len(verify_reader.pages) == 0:
                    return False, "Temp PDF has no pages"

            # Success - replace original
            shutil.copy2(temp_path, pdf_path)
            Path(temp_path).unlink()

            return True, "Success"

        except Exception as e:
            # Clean up temp file on error
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    # Configuration - UPDATE THESE PATHS FOR YOUR SYSTEM
    ZOTERO_DB = r"X:\Zotero\zotero.sqlite"
    ZOTERO_STORAGE = r"X:\Zotero\storage"

    print("=" * 60)
    print("FAST Zotero Metadata Embedder")
    print("=" * 60)
    print()

    # Get metadata from Zotero
    print("Reading Zotero database...")
    metadata_map = get_zotero_metadata(ZOTERO_DB, ZOTERO_STORAGE)
    print(f"✓ Found {len(metadata_map)} PDFs with metadata")
    print()

    # Process each PDF
    success_count = 0
    error_count = 0
    skipped_count = 0

    for pdf_path_str, metadata in metadata_map.items():
        pdf_path = Path(pdf_path_str)

        # Double-check file exists (should already be filtered)
        if not pdf_path.exists():
            print(f"⊘ SKIP: {pdf_path.name} (file not found)")
            skipped_count += 1
            continue

        print(f"Processing: {pdf_path.name}")

        # Update metadata
        success, message = update_pdf_metadata_fast(pdf_path, metadata)

        if success:
            print(f"  ✓ {message}")
            success_count += 1
        else:
            print(f"  ✗ {message}")
            error_count += 1

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total PDFs:    {len(metadata_map)}")
    print(f"Success:       {success_count}")
    print(f"Errors:        {error_count}")
    print(f"Skipped:       {skipped_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
