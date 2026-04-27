# fulltext0 - A lightweight full-text search engine

A fast, lightweight full-text search engine library with native support for CJK (Chinese/Japanese/Korean) text indexing and search.

## Features

- **CJK N-gram Tokenization**: Automatically generates bigrams and unigrams for CJK characters
- **VarInt Compression**: Efficient posting list compression using variable-length integer encoding
- **Memory-mapped Index**: Fast query execution with mmap-based index access
- **Python ctypes Interface**: Easy-to-use Python bindings with zero compilation required for basic usage
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

```bash
pip install fulltext0
```

## Quick Start

### Building an Index

```python
import fulltext0

# Build index from a corpus file (one document per line)
fulltext0.build(
    corpus_path="documents.txt",
    idx_path="my_index.idx",
    off_path="my_index.offsets"
)
```

### Searching

```python
import fulltext0

# Open the index
with fulltext0.Index("my_index.idx", "my_index.offsets") as idx:
    # Search for documents
    doc_ids = idx.query("system")
    print(f"Found {len(doc_ids)} documents")

    # Get the actual document text
    lines = idx.get_lines("documents.txt", doc_ids[:5])
    for line in lines:
        print(line)
```

### Tokenization

```python
import fulltext0

# Tokenize text (CJK characters are split into bigrams and unigrams)
tokens = fulltext0.tokenize("Hello 系統設計 world")
# Returns: ['hello', '系', '統設', '統', '系統', '設', '計', 'world']
```

## How It Works

### CJK N-gram Tokenization

For Chinese, Japanese, and Korean text, the engine generates:
- **Bigrams**: Consecutive character pairs (e.g., "系統" for "系" + "統")
- **Unigrams**: Individual characters (e.g., "系", "統")

This approach handles the lack of word boundaries in CJK scripts without requiring a dictionary.

### Inverted Index

The engine builds an inverted index mapping each token to the list of document IDs containing that token. Query execution performs an AND intersection across all query tokens.

### Compression

Posting lists are compressed using VarInt (variable-length integer) delta encoding, reducing index size significantly for large document sets.

## API Reference

### fulltext0.build(corpus_path, idx_path=None, off_path=None)

Build an inverted index from a corpus file.

**Parameters:**
- `corpus_path` (str): Path to the corpus file (one document per line)
- `idx_path` (str, optional): Path for the index file. Defaults to `_index/data.idx`
- `off_path` (str, optional): Path for the offsets file. Defaults to `_index/offsets.bin`

**Returns:** `int` - 0 on success

### fulltext0.Index(idx_path=None, off_path=None)

Open an existing index for searching.

**Parameters:**
- `idx_path` (str, optional): Path to the index file
- `off_path` (str, optional): Path to the offsets file

**Methods:**

- `stats()` → `IndexStats`: Get index statistics (number of terms, documents)
- `query(query_str)` → `List[int]`: Search for documents matching the query, returns list of doc IDs
- `get_lines(corpus_path, doc_ids)` → `List[str]`: Retrieve the text of documents by ID
- `close()`: Close the index

**Context Manager:** Supports `with` statement for automatic cleanup.

### fulltext0.tokenize(text) → List[str]

Tokenize text into search tokens.

**Parameters:**
- `text` (str): Text to tokenize

**Returns:** List of tokens

## Performance

- Indexes 1000 documents in under 1 second
- Query execution in milliseconds
- ~27% of original posting list size with VarInt compression
- O(1) term lookup using hash tables

## Requirements

- Python 3.8+
- C compiler (gcc, clang, or MSVC on Windows)
- Works on Windows, macOS, and Linux

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.