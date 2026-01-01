# Zotero Metadata Embedder

A fast Python script that embeds bibliographic metadata from your Zotero library directly into PDF files.

## Features

- **Fast**: Uses `pypdf`'s `clone_from` feature to update metadata without loading entire PDFs into memory
- **Safe**: Writes to temporary files first, only replacing originals after verification
- **Comprehensive**: Extracts title, authors, DOI, journal, volume, issue, pages, publisher, and date
- **Read-only**: Accesses Zotero database in read-only mode - no risk of database corruption

## Requirements

- Python 3.7+
- Zotero 7
- Required packages:
  ```bash
  pip install pypdf
  ```

## Configuration

Edit the paths at the top of `zotero_metadata_embedder.py`:

```python
ZOTERO_DB = r"X:\Zotero\zotero.sqlite"
ZOTERO_STORAGE = r"X:\Zotero\storage"
```

Default Zotero locations:
- **Windows**: `C:\Users\<username>\Zotero`
- **macOS**: `~/Zotero`
- **Linux**: `~/Zotero`

## Usage

```bash
python zotero_metadata_embedder.py
```

The script will:
1. Read metadata from your Zotero database
2. Find all PDFs with parent items (papers with metadata)
3. Embed metadata into each PDF file
4. Show progress and summary

### Example Output

```
============================================================
FAST Zotero Metadata Embedder (CORRECTED)
============================================================

Reading Zotero database...
✓ Found 1193 PDFs with metadata

Processing: Smith et al. - 2020 - Title.pdf
  ✓ Success
Processing: Jones - 2019 - Another paper.pdf
  ✓ Success
...

============================================================
SUMMARY
============================================================
Total PDFs:    1193
Success:       1150
Errors:        0
Skipped:       43
============================================================
```

## How It Works

The script:
1. Connects to Zotero's SQLite database in read-only immutable mode
2. Queries for PDF attachments and their parent items' metadata
3. For each PDF:
   - Validates the file exists and is readable
   - Clones the PDF structure using `PdfWriter(clone_from=...)`
   - Preserves existing metadata and adds Zotero metadata
   - Writes to a temporary file
   - Verifies the temporary file is valid
   - Replaces the original only if everything succeeded

## Metadata Fields

The following fields are embedded into PDFs (when available):

- `/Title` - Paper title
- `/Author` - All authors (semicolon-separated)
- `/DOI` - Digital Object Identifier
- `/Date` - Publication date
- `/Journal` - Journal/publication name
- `/Volume` - Volume number
- `/Issue` - Issue number
- `/Pages` - Page range
- `/Publisher` - Publisher name

## Safety Features

- **Read-only database access**: Uses `immutable=1` flag to prevent any writes to Zotero database
- **Temporary file verification**: Only replaces original if temp file is valid
- **Existing metadata preservation**: Keeps all existing PDF metadata
- **File validation**: Checks PDFs have pages before and after modification

## Use Cases

- **Better file organization**: Metadata visible in file managers and PDF readers
- **Indexing systems**: Helps document indexing tools like LlamaIndex extract citation info
- **Backup metadata**: Metadata travels with the PDF even outside Zotero
- **Search enhancement**: File search tools can index embedded metadata

## Compatibility

- Tested with **Zotero 7**
- Works on Windows, macOS, and Linux
- Compatible with any PDF reader that displays metadata

## Performance

Processing speed: ~1-2 seconds per PDF (vs. ~2 minutes with page-copying approaches)

For 1,193 PDFs: ~30-40 minutes total

## Limitations

- Only processes PDFs that are stored in Zotero's storage folder
- Requires parent items with metadata (won't process standalone PDFs)
- Skips files that don't exist or can't be read

## Troubleshooting

**Database locked error**: Close Zotero before running the script, or wait a moment and retry

**File not found errors**: The script only processes files that exist - skipped files may have been moved or deleted

**Permission errors**: Ensure you have write access to the Zotero storage directory

## License

MIT License - feel free to modify and distribute

## Integration with LlamaIndex

This script pairs well with document indexing systems. After embedding metadata, tools like LlamaIndex can automatically extract citation information when building search indexes.

See the companion `build_index_with_citations.py` script for an example of building a FAISS index with automatic citation extraction.
