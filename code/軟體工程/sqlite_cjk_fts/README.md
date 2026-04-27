# sqlite-cjk-fts

CJK Bigram Tokenizer for SQLite FTS5 — enables full-text search on Chinese, Japanese, and Korean text.

## Features

- **Bigram tokenization**: Generates overlapping bigrams for CJK characters, so any 2-character substring can be matched.
- **Unicode-aware**: Handles Chinese/Japanese/Korean Han characters, Hiragana, Katakana, and Hangul.
- **ASCII/Latin support**: Falls back to standard word boundary splitting for non-CJK text.
- **Cross-platform**: Supports macOS (`.dylib`), Linux (`.so`), and Windows (`.dll`).
- **Auto-build**: If no pre-compiled extension is found, automatically builds from source.

## Installation

```bash
pip install sqlite-cjk-fts
```

### macOS Note

Apple's pre-installed Python does **not** support `load_extension()`. On macOS, use Homebrew Python:

```bash
brew install python@3.13
/opt/homebrew/bin/python3 your_script.py
```

Or create a virtual environment with Homebrew Python:

```bash
/opt/homebrew/bin/python3 -m venv .venv
source .venv/bin/activate
pip install sqlite-cjk-fts
```

### Linux Requirements

On Linux, ensure you have build tools installed:

```bash
# Ubuntu/Debian
apt install build-essential libsqlite3-dev

# Fedora/RHEL
dnf install gcc sqlite-devel
```

Then install:

```bash
pip install sqlite-cjk-fts
```

The package will automatically compile the C extension from source.

### Windows Requirements

On Windows, install Visual Studio Build Tools or MinGW-w64, then:

```powershell
pip install sqlite-cjk-fts
```

## Quick Start

```python
from sqlite_cjk_fts import connect, create_table, insert, search

# Open database (auto-loads or auto-builds the CJK tokenizer)
db = connect(":memory:")

# Create FTS5 table with CJK bigram tokenizer
create_table(db, "docs", ["title", "body"])

# Insert data
insert(db, "docs", ("天氣預報", "今天天氣非常好，適合出門散步"))
insert(db, "docs", ("新聞頭條", "今日股市大漲，創下歷史新高"))

# Search
results = search(db, "docs", "天氣")
print(results)
# [('天氣預報', '今天天氣非常好，適合出門散步')]

results = search(db, "docs", "今天")
print(results)
# [('天氣預報', '今天天氣非常好，適合出門散步')]

results = search(db, "docs", "股市")
print(results)
# [('新聞頭條', '今日股市大漲，創下歷史新高')]
```

## API

### `sqlite_cjk_fts.connect(database, **kwargs)`

Open a SQLite database with the CJK tokenizer auto-loaded.

```python
from sqlite_cjk_fts import connect

db = connect("myapp.db")           # file-based
db = connect(":memory:")           # in-memory
db = connect(":memory:", ext_path="/custom/path/to/libcjkfts.so")  # custom extension
```

### `sqlite_cjk_fts.create_table(conn, name, columns, tokenizer="cjk_bigram")`

Create an FTS5 virtual table.

```python
from sqlite_cjk_fts import connect, create_table

db = connect(":memory:")
create_table(db, "articles", ["title", "content"])
```

### `sqlite_cjk_fts.insert(conn, table, values)`

Insert a row into an FTS5 table.

```python
from sqlite_cjk_fts import insert

insert(db, "docs", ("title here", "body text here"))
# or with named parameters:
insert(db, "docs", {"title": "title here", "body": "body text here"})
```

### `sqlite_cjk_fts.search(conn, table, query, columns=None, limit=0)`

Search the FTS5 table.

```python
results = search(db, "docs", "天氣")           # all columns
results = search(db, "docs", "天氣", limit=10) # with limit
results = search(db, "docs", "天氣", columns=["title"])  # specific columns
```

### `sqlite_cjk_fts.build_extension(compiler=None, output_dir=None, verbose=False)`

Manually build the C extension from source.

```python
from sqlite_cjk_fts import build_extension

# Build with verbose output
ext_path = build_extension(verbose=True)
print(f"Built: {ext_path}")
```

### `sqlite_cjk_fts.get_ext_path(ext_path=None)`

Get the path to the extension file.

```python
from sqlite_cjk_fts import get_ext_path

path = get_ext_path()  # auto-detect
path = get_ext_path("/custom/path/libcjkfts.so")  # explicit path
```

### `sqlite_cjk_fts.Connection`

The extended `sqlite3.Connection` class. Use via `connect()`.

### `sqlite_cjk_fts.Tokenizer`

The tokenizer name constant: `"cjk_bigram"`.

## Using with raw sqlite3

If you prefer the standard `sqlite3` module, load the extension manually:

```python
import sqlite3
from sqlite_cjk_fts import get_ext_path

db = sqlite3.connect(":memory:")
db.execute("PRAGMA enable_load_extension=1")
db.load_extension(get_ext_path())  # or explicit path
db.execute("CREATE VIRTUAL TABLE docs USING fts5(content, tokenize='cjk_bigram')")
```

## Platform-Specific Notes

| Platform | Extension | Build Command |
|----------|-----------|---------------|
| macOS    | `.dylib`  | `gcc -fPIC -shared cjk_tokenizer.c -o libcjkfts.dylib` |
| Linux    | `.so`     | `gcc -fPIC -shared cjk_tokenizer.c -o libcjkfts.so` |
| Windows  | `.dll`    | `cl /LD cjk_tokenizer.c /Fe:libcjkfts.dll` |

## License

MIT